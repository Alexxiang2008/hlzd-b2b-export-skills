#!/usr/bin/env python3
r"""
HLZD-视频生成 - 主控编排器
完整流程：
  1. 加载 entities.json（或自动 B2B 闭环）
  2. 构造 prompt
  3. 调 Agnes 客户端生成视频片段
  4. 多段拼接 + BGM + 字幕
  5. 输出到 outputs/videos/YYYY-MM-DD/

用法:
  py scripts/orchestrator.py --entities entities.json
  py scripts/orchestrator.py --auto --product-name 石油套管 --duration 10
  py scripts/orchestrator.py --auto --report "D:\xxx\石油套管B2B市场调研报告.md"
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Windows UTF-8 兼容（Python 3.7+ 默认 UTF-8，无需 wrapper）
# 早期版本可用：sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Windows UTF-8 兼容（Python 3.7+ 默认 UTF-8，无需 wrapper）

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from prompt_builder import build_video_prompt
from agnes_video_client import generate_and_download
from video_postprocess import finalize_video
from subtitle_manager import generate_subtitles


# ============ 输出管理 ============
def get_output_paths(product_name):
    """生成输出路径"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.now().strftime('%H%M%S')

    # 产品名清洗（去除路径非法字符）
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in product_name)

    base_dir = os.path.join(SKILL_ROOT, 'outputs')
    videos_dir = os.path.join(base_dir, 'videos', date_str)
    history_dir = os.path.join(base_dir, 'history')
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    segments_prefix = os.path.join(videos_dir, f'{safe_name}_{time_str}_seg')
    final_path = os.path.join(videos_dir, f'{safe_name}_{time_str}.mp4')
    history_path = os.path.join(history_dir, f'{date_str}.json')

    return {
        'segments_prefix': segments_prefix,
        'final_path': final_path,
        'history_path': history_path,
        'date_str': date_str,
        'safe_name': safe_name,
        'time_str': time_str,
    }


def append_history(history_path, entry):
    """追加历史记录"""
    # 顶层 date 用 entry 的 timestamp 或当前日期
    entry_date = entry.get('date') or entry.get('timestamp', '')[:10] or datetime.now().strftime('%Y-%m-%d')
    history = {'date': entry_date, 'entries': []}
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            pass

    history['entries'].append(entry)

    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ============ 视频分段策略 ============
def split_into_segments(duration):
    """
    根据总时长拆分为多段（每段 ≤ 18s）
    Returns: list of duration_sec
    """
    if duration <= 18:
        return [duration]

    # 每段 15s，留 3s 余量给过渡
    segment_dur = 15
    segments = []
    remaining = duration
    while remaining > 18:
        segments.append(segment_dur)
        remaining -= segment_dur
    if remaining > 0:
        segments.append(remaining)
    return segments


def build_segment_prompts(base_prompt, num_segments, scene_motion_key='orbit'):
    """
    为每个分段构造不同的 prompt（避免内容重复）
    简单策略：每个分段用不同的镜头描述
    """
    if num_segments == 1:
        return [base_prompt]

    motion_variants = {
        'orbit': [
            'starting from front view, slow 360 degree orbit',
            'continuing rotation, mid-angle view',
            'final rotation, top-down perspective',
            'concluding with detailed close-up',
        ],
        'factory_run': [
            'wide establishing shot of factory floor',
            'medium shot of machinery in operation',
            'close-up of moving parts and mechanical details',
            'pull-back revealing full production context',
        ],
        'push_in': [
            'wide establishing shot of the product',
            'medium shot approaching the product',
            'close-up revealing material details',
            'macro shot of intricate craftsmanship',
        ],
        'site_demo': [
            'wide establishing shot of construction site',
            'medium shot of equipment in operation',
            'close-up of work being performed',
            'concluding wide shot of completed work',
        ],
    }

    variants = motion_variants.get(scene_motion_key, [base_prompt] * num_segments)
    prompts = []
    for i in range(num_segments):
        variant = variants[i] if i < len(variants) else base_prompt
        # 替换 prompt 中的动作描述部分
        prompts.append(f"{variant}, {base_prompt}")
    return prompts


# ============ 主流程 ============
def run(entities, num_candidates=1):
    """
    主流程编排
    entities: 实体字典
    num_candidates: 每个片段的候选数（多次生成+选最佳）
    Returns: dict {final_path, history_entry}
    """
    product_name = entities.get('product_name') or 'unnamed'
    print(f"\n[开始] 产品: {product_name}", file=sys.stderr)
    if num_candidates > 1:
        print(f"[多次生成] 每个片段 {num_candidates} 个候选，自动选最佳", file=sys.stderr)
    print(f"[参数] {json.dumps({k: v for k, v in entities.items() if k != 'reference_images'}, ensure_ascii=False, indent=2)}", file=sys.stderr)

    # 1. 构造 prompt
    # 强制 CLI 传入的 capability 最高优先级（避免 prompt_builder 自动升级 i2v→multi_i2v）
    user_capability = entities.get('capability')
    prompt_data = build_video_prompt(entities)
    if user_capability and prompt_data.get('capability') != user_capability:
        print(f"[覆盖] CLI capability={user_capability!r} 覆盖 prompt_builder={prompt_data.get('capability')!r}", file=sys.stderr)
        prompt_data['capability'] = user_capability
    print(f"\n[Prompt] {prompt_data['prompt']}", file=sys.stderr)

    # 2. 分段策略
    duration = prompt_data['duration']
    segments_dur = split_into_segments(duration)
    print(f"[分段] 总时长 {duration}s → 拆分为 {len(segments_dur)} 段: {segments_dur}", file=sys.stderr)

    # 3. 多段 prompt（避免重复）
    base_prompt = prompt_data['prompt']
    segment_prompts = build_segment_prompts(
        base_prompt, len(segments_dur), entities.get('scene_motion', 'orbit')
    )

    # 4. 输出路径
    paths = get_output_paths(product_name)

    # 5. 参考图处理
    image_url = prompt_data.get('image_url', '')
    image_urls = prompt_data.get('image_urls', [])
    capability = prompt_data['capability']

    # 5.1 自动上传本地图片到 imgbb（I2V 模式需要公网 URL）
    from b2b_research_parser import upload_to_public_url

    def to_public_url(value):
        """把本地路径或 dict 转公网 URL；已是 http URL 则原样返回"""
        if not value:
            return ''
        if isinstance(value, str):
            if value.startswith('http://') or value.startswith('https://'):
                return value
            # 本地路径
            print(f"[上传] 本地图片 → imgbb: {os.path.basename(value)}", file=sys.stderr)
            return upload_to_public_url(value)
        if isinstance(value, dict):
            # {path, mtime, filename} 格式
            local = value.get('path', '')
            if not local:
                return ''
            print(f"[上传] 本地图片 → imgbb: {os.path.basename(local)}", file=sys.stderr)
            return upload_to_public_url(local)
        return ''

    # 5.1 先根据 capability 决定要上传几张图（节省 imgbb 配额 + 避免 Agnes 报错）
    from b2b_research_parser import upload_to_public_url

    def to_public_url(value):
        """把本地路径或 dict 转公网 URL；已是 http URL 则原样返回"""
        if not value:
            return ''
        if isinstance(value, str):
            if value.startswith('http://') or value.startswith('https://'):
                return value
            # 本地路径
            print(f"[上传] 本地图片 → imgbb: {os.path.basename(value)}", file=sys.stderr)
            return upload_to_public_url(value)
        if isinstance(value, dict):
            local = value.get('path', '')
            if not local:
                return ''
            print(f"[上传] 本地图片 → imgbb: {os.path.basename(local)}", file=sys.stderr)
            return upload_to_public_url(local)
        return ''

    # I2V 只支持 1 张图：先选图，再上传
    if capability == 'i2v':
        # 选图：image_url 优先；否则从 image_urls 取最新
        if image_url:
            chosen = image_url
        elif image_urls:
            chosen = image_urls[0]
            print(f"[提示] I2V 模式仅支持 1 张图，已取最新: {os.path.basename(chosen.get('path', chosen) if isinstance(chosen, dict) else chosen)}", file=sys.stderr)
        else:
            chosen = ''
        image_url = to_public_url(chosen)
        image_urls = []
        image_urls_for_segments = [image_url] * len(segments_dur) if image_url else []
    elif capability in ('multi_i2v', 'keyframes'):
        # 多图：上传所有图（每段用不同子集）
        image_url = to_public_url(image_url) if image_url else ''
        image_urls = [to_public_url(u) for u in image_urls if u]
        image_urls_for_segments = image_urls[:len(segments_dur)] if image_urls else []
    else:
        # T2V 不需要图
        image_url = ''
        image_urls = []
        image_urls_for_segments = []

    # 6. 生成所有片段（支持多次候选）
    from quality_scorer import score_video, pick_best

    segment_paths = []
    segment_candidates_meta = []  # 记录每个片段所有候选的评分
    for i, (seg_dur, seg_prompt) in enumerate(zip(segments_dur, segment_prompts)):
        # 不同段用不同图（如果有）
        seg_image = image_urls_for_segments[i] if i < len(image_urls_for_segments) else (image_url if image_url else None)
        seg_images_list = None
        seg_image_single = None

        if capability == 'i2v':
            seg_image_single = seg_image
        elif capability in ('multi_i2v', 'keyframes'):
            seg_images_list = image_urls[i:i+2] if image_urls else None
            if not seg_images_list or len(seg_images_list) < 2:
                seg_images_list = image_urls[:2] if image_urls else None

        print(f"\n[生成] 片段 {i+1}/{len(segments_dur)}: {seg_dur}s × {num_candidates} 候选", file=sys.stderr)

        # 6.1 多次生成候选
        candidate_paths = []
        candidate_meta = []
        base_seed = prompt_data.get('seed') or 0
        for cand_idx in range(num_candidates):
            cand_path = f"{paths['segments_prefix']}{i:02d}_cand{cand_idx}.mp4"

            kwargs = {
                'duration': seg_dur,
                'aspect_ratio': prompt_data['aspect_ratio'],
                'resolution': prompt_data['resolution'],
                # 不同候选用不同 seed（0 = None 时随机）
                'seed': (base_seed + cand_idx) if base_seed else None,
                'negative_prompt': prompt_data.get('negative_prompt'),
                'output_path': cand_path,
            }
            if capability == 'i2v':
                kwargs['image_url'] = seg_image_single
                # 防御性：清空 image_urls 避免冲突
                kwargs.pop('image_urls', None)
            elif capability in ('multi_i2v', 'keyframes'):
                kwargs['image_urls'] = seg_images_list
                kwargs.pop('image_url', None)

            try:
                result = generate_and_download(capability, seg_prompt, **kwargs)
                candidate_paths.append(result['local_path'])
            except SystemExit:
                print(f"[错误] 片段 {i+1} 候选 {cand_idx} 生成失败", file=sys.stderr)
                raise

        # 6.2 评分并选最佳
        target = {'duration': seg_dur, 'min_resolution': 640}
        # 先全部评分
        all_scores = []
        for cp in candidate_paths:
            sc = score_video(cp, target)
            sc['path'] = cp
            all_scores.append(sc)
        # 按分数降序
        all_scores.sort(key=lambda r: r.get('score', 0), reverse=True)

        # 打印评分明细
        for r in all_scores:
            print(f"[评分] {os.path.basename(r['path'])}: {r['score']}/100 "
                  f"(大小={r.get('breakdown', {}).get('size', 0)} "
                  f"分辨率={r.get('breakdown', {}).get('resolution', 0)} "
                  f"时长={r.get('breakdown', {}).get('duration', 0)} "
                  f"码率={r.get('breakdown', {}).get('bitrate', 0)} "
                  f"帧={r.get('breakdown', {}).get('frames', 0)})",
                  file=sys.stderr)

        # 选最佳
        best = all_scores[0]
        best_path = best['path']
        print(f"[选中] {os.path.basename(best_path)} → {best['score']}/100", file=sys.stderr)

        # 记录全部候选（不只是 best）
        segment_candidates_meta.append({
            'segment_index': i,
            'duration': seg_dur,
            'candidates': [
                {'path': r['path'], 'score': r['score'], 'info': r.get('info')}
                for r in all_scores
            ],
            'selected': best_path,
        })

        # 清理次优候选（保留 top-1）
        for r in all_scores[1:]:
            if os.path.exists(r['path']):
                os.remove(r['path'])
                print(f"[清理] 删除次优: {os.path.basename(r['path'])}", file=sys.stderr)

        segment_paths.append(best_path)

    # 7. 字幕
    subtitles = None
    if entities.get('subtitle', True):
        # 根据 product_name 推断 product_key
        product_key = _guess_product_key(product_name)
        if product_key:
            lang = entities.get('subtitle_lang', 'en')
            subtitles = generate_subtitles(product_key, lang=lang, max_tags=3)
            print(f"[字幕] {lang}: {len(subtitles)} 条", file=sys.stderr)

    # 8. 后处理（拼接 + BGM + 字幕）
    print(f"\n[后处理] 拼接 + BGM + 字幕", file=sys.stderr)
    bgm_style = entities.get('bgm_style', 'corporate')
    subtitle_lang = entities.get('subtitle_lang', 'en')

    finalize_video(
        segments=segment_paths,
        output_path=paths['final_path'],
        bgm_style=bgm_style,
        subtitles=subtitles,
        subtitle_lang=subtitle_lang,
        transition='fade',
    )

    # 9. 历史记录
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'capability': capability,
        'product_name': product_name,
        'product_category': entities.get('product_category'),
        'model': 'agnes-video-v2.0',
        'params': {
            'prompt': base_prompt,
            'duration': duration,
            'aspect_ratio': prompt_data['aspect_ratio'],
            'resolution': prompt_data['resolution'],
            'bgm_style': bgm_style,
            'subtitle_lang': subtitle_lang,
            'segments': len(segments_dur),
            'num_candidates': num_candidates,
        },
        'image_urls': image_urls[:4] if image_urls else ([image_url] if image_url else []),
        'video_url': None,  # 暂不上传
        'local_path': paths['final_path'],
        'segment_paths': segment_paths,
        'segment_candidates': segment_candidates_meta,  # 多次生成的评分记录
        'source_report': entities.get('source_report'),
        'cost': 0.0,  # 当前限时免费
    }
    append_history(paths['history_path'], history_entry)

    print(f"\n[完成] {paths['final_path']}", file=sys.stderr)

    return {
        'final_path': paths['final_path'],
        'history_entry': history_entry,
    }


def _guess_product_key(product_name):
    """根据产品名猜测 product_key"""
    from prompt_builder import match_product
    # 简单尝试在 machinery/equipment/materials 三个类别里找
    for cat in ('machinery', 'equipment', 'materials'):
        key, _ = match_product(product_name, cat)
        if key:
            return key
    return None


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='HLZD-视频生成 orchestrator')
    parser.add_argument('--entities', help='entities JSON 路径')
    parser.add_argument('--auto', action='store_true', help='自动闭环检测 B2B 报告 + 图片历史')
    parser.add_argument('--report', help='指定 B2B 报告路径')
    parser.add_argument('--product-name', help='产品名（自动检测时可选）')
    parser.add_argument('--capability', choices=['i2v', 'multi_i2v', 'keyframes', 't2v'], default='i2v')
    parser.add_argument('--duration', type=int, default=10, help='总时长（秒）')
    parser.add_argument('--aspect-ratio', default='16:9')
    parser.add_argument('--bgm-style', default='corporate', choices=['corporate', 'industrial', 'upbeat', 'epic', 'none'])
    parser.add_argument('--subtitle-lang', default='en', choices=['en', 'zh', 'bilingual'])
    parser.add_argument('--no-subtitle', action='store_true', help='关闭字幕')
    parser.add_argument('--quantity', type=int, default=1, help='生成候选数')
    parser.add_argument('--num-candidates', type=int, default=1, help='每个片段多次生成候选数（自动选最佳）')
    parser.add_argument('--reference-image', help='单张参考图（本地路径或公网URL，I2V 用）')
    parser.add_argument('--reference-images', help='多张参考图（逗号分隔，multi_i2v/keyframes 用）')
    args = parser.parse_args()

    # 1. 加载 entities
    if args.entities:
        with open(args.entities, 'r', encoding='utf-8') as f:
            entities = json.load(f)
    elif args.auto or args.report or args.product_name:
        from b2b_research_parser import auto_detect_all
        entities = auto_detect_all(report_path=args.report, max_images=4)
        if args.product_name:
            entities['product_name'] = args.product_name
    else:
        print("[错误] 需要 --entities 或 --auto/--report/--product-name", file=sys.stderr)
        sys.exit(1)

    # 2. CLI 参数覆盖
    entities['capability'] = args.capability
    entities['duration'] = args.duration
    entities['aspect_ratio'] = args.aspect_ratio
    entities['bgm_style'] = args.bgm_style
    entities['subtitle_lang'] = args.subtitle_lang
    entities['subtitle'] = not args.no_subtitle

    # 2.1 CLI 参考图覆盖
    if args.reference_image:
        entities['reference_image'] = args.reference_image
        print(f"[I2V] 使用指定参考图: {args.reference_image}", file=sys.stderr)
    if args.reference_images:
        entities['reference_images'] = [u.strip() for u in args.reference_images.split(',') if u.strip()]
        print(f"[I2V] 使用 {len(entities['reference_images'])} 张参考图", file=sys.stderr)

    # 3. 批量
    results = []
    for i in range(args.quantity):
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"[批量] {i+1}/{args.quantity}", file=sys.stderr)
        result = run(entities, num_candidates=args.num_candidates)
        results.append(result)

    # 4. 输出
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[全部完成] {len(results)} 个视频", file=sys.stderr)
    for r in results:
        print(f"  - {r['final_path']}", file=sys.stderr)

    # JSON 输出
    print(json.dumps({
        'count': len(results),
        'videos': [{'path': r['final_path']} for r in results]
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()