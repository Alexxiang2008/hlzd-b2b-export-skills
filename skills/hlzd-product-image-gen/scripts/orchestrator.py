#!/usr/bin/env python3
"""
HLZD-图片生成 - 主调度（SKILL.md 实际调用入口）
用法:
  # T2I
  py scripts/orchestrator.py --entities entities.json --capability t2i

  # I2I（带参考图 URL）
  py scripts/orchestrator.py --entities entities.json --capability i2i --reference https://example.com/ref.jpg

  # 抠图（本地路径）
  py scripts/orchestrator.py --capability remove_bg --input D:\test\valve.jpg --output D:\test\valve_no_bg.png

  # B2B 闭环
  py scripts/orchestrator.py --auto-b2b --capability t2i
依赖: 同 agnes_client / image_enhancer
"""

import argparse
import json
import os
import sys
import io
import time
import warnings

warnings.filterwarnings('ignore')


def _ensure_utf8_stdio():
    """幂等地包装 stdout/stderr 为 UTF-8（避免重复包装导致状态损坏）"""
    if sys.platform != 'win32':
        return
    for _name in ('stdout', 'stderr'):
        _stream = getattr(sys, _name, None)
        if _stream is None or not hasattr(_stream, 'buffer'):
            continue
        _encoding = getattr(_stream, 'encoding', None) or ''
        if 'utf-8' in _encoding.lower():
            continue
        _wrapper = io.TextIOWrapper(_stream.buffer, encoding='utf-8', errors='replace')
        setattr(sys, _name, _wrapper)


_ensure_utf8_stdio()


# 导入同目录模块（延迟到函数内，避免 --help 时触发 GBK 头重复包装问题）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


# ============ 路由 ============
def run_t2i(entities):
    """T2I 文生图路由"""
    # 延迟导入：避免 --help 时触发子模块加载链
    from prompt_builder import build_prompt
    from agnes_client import generate_t2i
    from output_manager import save_image, save_history_entry

    prompt_data = build_prompt(entities)
    prompt = prompt_data['prompt']
    size = prompt_data['size']
    quantity = prompt_data.get('quantity', 1)

    print(f"[Orchestrator] T2I: {prompt[:80]}...", file=sys.stderr)
    print(f"[Orchestrator] size={size}, quantity={quantity}", file=sys.stderr)

    results = []
    for i in range(quantity):
        image_url = generate_t2i(prompt, size, return_url=True)
        product_name = entities.get('product_name', 'image')
        suggested = f"{product_name}_{i+1:03d}.png"

        local_path = save_image(image_url, suggested)

        # 保存历史
        meta = {
            'capability': 't2i',
            'product_name': product_name,
            'product_category': entities.get('product_category'),
            'model': 'agnes-image-2.1-flash',
            'params': {'prompt': prompt, 'size': size, 'index': i+1},
            'cost': 0.0,  # 当前促销价
            'source_report': entities.get('source_report')
        }
        entry = save_history_entry(meta, image_url=image_url, local_path=local_path)
        results.append(entry)

    return results


def run_i2i(entities, reference_image):
    """I2I 图生图路由"""
    from prompt_builder import build_prompt
    from agnes_client import generate_i2i
    from output_manager import save_image, save_history_entry

    prompt_data = build_prompt(entities)
    prompt = prompt_data['prompt']
    size = prompt_data['size']

    print(f"[Orchestrator] I2I: {prompt[:80]}...", file=sys.stderr)
    print(f"[Orchestrator] reference={reference_image[:80]}", file=sys.stderr)

    # 本地文件 → 转 base64 data URI（Agnes 支持）
    if os.path.exists(reference_image):
        print(f"[Orchestrator] 检测到本地参考图，转 base64 data URI...", file=sys.stderr)
        reference_image = _local_path_to_data_uri(reference_image)

    image_url = generate_i2i(prompt, reference_image, size, return_url=True)
    product_name = entities.get('product_name', 'image')
    suggested = f"{product_name}_i2i_{int(time.time())}.png"

    local_path = save_image(image_url, suggested)

    meta = {
        'capability': 'i2i',
        'product_name': product_name,
        'product_category': entities.get('product_category'),
        'model': 'agnes-image-2.1-flash',
        'params': {'prompt': prompt, 'size': size, 'reference': 'local_or_url'},
        'cost': 0.0,
        'source_report': entities.get('source_report')
    }
    entry = save_history_entry(meta, image_url=image_url, local_path=local_path)
    return [entry]


def _local_path_to_data_uri(local_path):
    """
    本地图片路径转 base64 data URI
    供 Agnes I2I API 使用（避免依赖公网 URL）

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件不是图片格式
        RuntimeError: 文件过大（Agnes 限制 ~10MB）
    """
    import base64
    import mimetypes

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"参考图不存在: {local_path}")

    # MIME 类型推断
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type or not mime_type.startswith('image/'):
        raise ValueError(f"文件不是图片格式: {local_path} (mime={mime_type})")

    # 读取 + 检查大小（Agnes 限制 ~10MB）
    with open(local_path, 'rb') as f:
        img_data = f.read()
    if len(img_data) > 10 * 1024 * 1024:
        raise RuntimeError(
            f"参考图过大: {len(img_data) / 1024 / 1024:.1f}MB > 10MB。\n"
            f"  建议先用 rembg 或 PIL 压缩后再使用。"
        )

    b64 = base64.b64encode(img_data).decode('utf-8')
    data_uri = f"data:{mime_type};base64,{b64}"
    print(f"[Orchestrator] 已转 data URI ({len(img_data) / 1024:.1f}KB, mime={mime_type})", file=sys.stderr)
    return data_uri


def run_remove_bg(input_path, output_path=None, bg_color=None):
    """抠图路由"""
    from image_enhancer import remove_background, change_background
    from output_manager import save_image, save_history_entry, GENERATED_DIR

    print(f"[Orchestrator] 抠图: {input_path}", file=sys.stderr)

    if not output_path:
        # 默认输出到 outputs/generated/{date}/
        date = time.strftime('%Y-%m-%d')
        base = os.path.splitext(os.path.basename(input_path))[0]
        if bg_color:
            output_path = os.path.join(GENERATED_DIR, date, f"{base}_{bg_color.lstrip('#')}.png")
        else:
            output_path = os.path.join(GENERATED_DIR, date, f"{base}_no_bg.png")

    if bg_color:
        change_background(input_path, output_path, bg_color)
    else:
        remove_background(input_path, output_path)

    # 保存历史（抠图无 cost）
    meta = {
        'capability': 'remove_bg',
        'product_name': os.path.splitext(os.path.basename(input_path))[0],
        'model': 'rembg-u2netp',
        'params': {'input': input_path, 'bg_color': bg_color},
        'cost': 0.0
    }
    entry = save_history_entry(meta, local_path=output_path)
    return [entry]


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='HLZD-图片生成 主调度')
    parser.add_argument('--entities', help='entities JSON 文件路径')
    parser.add_argument('--capability', choices=['t2i', 'i2i', 'remove_bg'], help='能力类型')
    parser.add_argument('--reference', help='I2I 参考图 URL 或本地路径')
    parser.add_argument('--input', help='抠图输入路径')
    parser.add_argument('--output', help='抠图输出路径')
    parser.add_argument('--bg-color', help='抠图背景色（如 #ffffff）')
    parser.add_argument('--auto-b2b', action='store_true', help='自动从 B2B 调研报告解析 entities')
    args = parser.parse_args()

    # ============ 处理 auto-b2b 模式 ============
    if args.auto_b2b:
        print("[Orchestrator] 自动解析 B2B 调研报告...", file=sys.stderr)
        from b2b_research_parser import extract_entities
        entities = extract_entities()
        if not entities:
            print("[错误] 未找到 B2B 调研报告或解析失败", file=sys.stderr)
            sys.exit(1)
        # 保存中间结果
        with open('b2b_entities.json', 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)
        args.entities = 'b2b_entities.json'
        print(f"[Orchestrator] 已生成 b2b_entities.json", file=sys.stderr)

    # ============ 路由 ============
    if args.capability == 't2i':
        if not args.entities:
            print("[错误] T2I 需要 --entities", file=sys.stderr)
            sys.exit(1)
        with open(args.entities, 'r', encoding='utf-8') as f:
            entities = json.load(f)
        results = run_t2i(entities)

    elif args.capability == 'i2i':
        if not args.entities:
            print("[错误] I2I 需要 --entities", file=sys.stderr)
            sys.exit(1)
        if not args.reference:
            print("[错误] I2I 需要 --reference（参考图 URL）", file=sys.stderr)
            sys.exit(1)
        with open(args.entities, 'r', encoding='utf-8') as f:
            entities = json.load(f)
        results = run_i2i(entities, args.reference)

    elif args.capability == 'remove_bg':
        if not args.input:
            print("[错误] 抠图需要 --input", file=sys.stderr)
            sys.exit(1)
        results = run_remove_bg(args.input, args.output, args.bg_color)

    else:
        print("[错误] 请指定 --capability（t2i/i2i/remove_bg）", file=sys.stderr)
        sys.exit(1)

    # 输出结果
    print("\n=== Orchestrator 完成 ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()