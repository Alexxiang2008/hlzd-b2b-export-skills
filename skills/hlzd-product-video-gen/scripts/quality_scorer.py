#!/usr/bin/env python3
"""
HLZD-视频生成 - 质量评分器
对多个候选 MP4 视频评分，选出最佳。

评分维度（加权）:
  1. 文件大小（清晰度代理）: 25%
  2. 分辨率（更高分更高）: 25%
  3. 时长准确度（接近目标时长）: 20%
  4. 码率（更高通常更清晰）: 20%
  5. 帧数完整度（8n+1 规则 + 接近 num_frames）: 10%

总分: 0-100
"""

import json
import os
import subprocess
import sys
from typing import Optional


# ============ FFprobe 工具 ============
def ffprobe_video(video_path: str) -> Optional[dict]:
    """
    用 ffprobe 获取视频元信息
    Returns: dict {width, height, duration, bit_rate, nb_frames, codec_name} or None
    """
    if not os.path.exists(video_path):
        return None

    try:
        # 用 ffprobe 拿流信息
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error',
                '-show_entries',
                'stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration,bit_rate,size',
                '-of', 'json',
                video_path,
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=15,
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        info = {'file_size': os.path.getsize(video_path)}

        # 取第一个视频流
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video' or 'width' in stream:
                info['codec_name'] = stream.get('codec_name')
                info['width'] = int(stream.get('width', 0))
                info['height'] = int(stream.get('height', 0))
                info['nb_frames'] = int(stream.get('nb_frames', 0) or 0)
                # r_frame_rate 格式 "24/1" → 24
                rate = stream.get('r_frame_rate', '0/1').split('/')
                info['fps'] = int(rate[0]) / int(rate[1]) if len(rate) == 2 and int(rate[1]) else 24
                break

        # format 级别信息
        fmt = data.get('format', {})
        info['duration'] = float(fmt.get('duration', 0) or 0)
        info['bit_rate'] = int(fmt.get('bit_rate', 0) or 0)

        return info
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as e:
        print(f"[警告] ffprobe 失败: {e}", file=sys.stderr)
        return None


# ============ 评分函数 ============
def score_video(video_path: str, target: dict = None) -> dict:
    """
    对单个视频评分
    target: dict {duration: 目标时长(秒), min_resolution: 最低分辨率}
    Returns: dict {score: 0-100, breakdown: {size, resolution, duration, bitrate, frames}, info: ffprobe结果}
    """
    target = target or {}
    target_duration = target.get('duration', 5)
    min_resolution = target.get('min_resolution', 640)  # Agnes 标准 720p 输出约 640x640

    info = ffprobe_video(video_path)
    if not info:
        return {'score': 0, 'breakdown': {}, 'info': {}, 'error': 'ffprobe failed'}

    breakdown = {}

    # 1. 文件大小（0-25 分）
    # Agnes 5秒视频约 250KB-1.5MB
    # 线性映射：< 200KB → 0 分，> 1.5MB → 25 分
    file_size_kb = info.get('file_size', 0) / 1024
    size_score = max(0, min(25, (file_size_kb - 200) / (1500 - 200) * 25))
    breakdown['size'] = round(size_score, 1)

    # 2. 分辨率（0-25 分）
    # 宽 * 高 / 1000 作为分母
    width = info.get('width', 0)
    height = info.get('height', 0)
    resolution = width * height
    if resolution >= min_resolution * min_resolution:
        res_score = 25  # 达到目标分辨率
    elif resolution > 0:
        res_score = (resolution / (min_resolution * min_resolution)) * 25
    else:
        res_score = 0
    breakdown['resolution'] = round(res_score, 1)

    # 3. 时长准确度（0-20 分）
    # 接近 target_duration 得分越高
    actual_duration = info.get('duration', 0)
    duration_diff = abs(actual_duration - target_duration)
    if duration_diff <= 0.3:  # 0.3 秒内
        dur_score = 20
    elif duration_diff <= 1.0:  # 1 秒内
        dur_score = 20 - (duration_diff - 0.3) * (20 / 0.7) * 0.5
    else:
        dur_score = max(0, 10 - (duration_diff - 1.0) * 2)
    breakdown['duration'] = round(dur_score, 1)

    # 4. 码率（0-20 分）
    # 5秒视频约 500Kbps-2Mbps
    bit_rate = info.get('bit_rate', 0) / 1000  # 转为 Kbps
    if bit_rate >= 1500:
        br_score = 20
    elif bit_rate >= 500:
        br_score = 10 + (bit_rate - 500) / 1000 * 10
    elif bit_rate > 0:
        br_score = (bit_rate / 500) * 10
    else:
        br_score = 0
    breakdown['bitrate'] = round(br_score, 1)

    # 5. 帧数完整度（0-10 分）
    # 检查帧数是否合理（4-8 fps/s × duration）
    nb_frames = info.get('nb_frames', 0)
    expected_frames_min = target_duration * 20  # 至少 20fps
    expected_frames_max = target_duration * 30  # 最多 30fps
    if expected_frames_min <= nb_frames <= expected_frames_max:
        frame_score = 10
    elif nb_frames > 0:
        frame_score = max(0, 10 - abs(nb_frames - (target_duration * 24)) / 10)
    else:
        frame_score = 0
    breakdown['frames'] = round(frame_score, 1)

    total = sum(breakdown.values())
    return {
        'score': round(total, 1),
        'breakdown': breakdown,
        'info': {
            'width': width,
            'height': height,
            'duration': actual_duration,
            'bit_rate': bit_rate,
            'nb_frames': nb_frames,
            'file_size_kb': round(file_size_kb, 1),
            'codec_name': info.get('codec_name'),
        }
    }


def pick_best(video_paths: list, target: dict = None, keep_top_n: int = 1) -> list:
    """
    对多个候选视频评分，按 score 排序，返回 [(path, score, breakdown, info), ...]
    keep_top_n: 保留前 N 个（默认 1，即只选最佳）
    """
    target = target or {}
    results = []
    for path in video_paths:
        result = score_video(path, target)
        result['path'] = path
        results.append(result)
        print(f"[评分] {os.path.basename(path)}: {result['score']}/100 "
              f"(大小={result.get('breakdown', {}).get('size', 0)} "
              f"分辨率={result.get('breakdown', {}).get('resolution', 0)} "
              f"时长={result.get('breakdown', {}).get('duration', 0)} "
              f"码率={result.get('breakdown', {}).get('bitrate', 0)} "
              f"帧={result.get('breakdown', {}).get('frames', 0)})",
              file=sys.stderr)

    # 按 score 降序
    results.sort(key=lambda r: r.get('score', 0), reverse=True)
    return results[:keep_top_n]


# ============ CLI ============
def main():
    import argparse
    parser = argparse.ArgumentParser(description='视频质量评分器')
    parser.add_argument('--inputs', required=True, help='候选视频路径，逗号分隔')
    parser.add_argument('--target-duration', type=float, default=5, help='目标时长（秒）')
    parser.add_argument('--min-resolution', type=int, default=640, help='最低分辨率')
    parser.add_argument('--keep-top-n', type=int, default=1, help='保留前 N 个')
    parser.add_argument('--out-json', help='保存评分结果到 JSON')
    parser.add_argument('--cleanup', action='store_true', help='删除非 top-N 候选')
    args = parser.parse_args()

    paths = [p.strip() for p in args.inputs.split(',') if p.strip()]
    target = {'duration': args.target_duration, 'min_resolution': args.min_resolution}
    top = pick_best(paths, target, args.keep_top_n)

    print("\n=== 评分结果 ===", file=sys.stderr)
    for i, r in enumerate(top, 1):
        print(f"#{i}: {r['path']} → {r['score']}/100", file=sys.stderr)

    if args.out_json:
        with open(args.out_json, 'w', encoding='utf-8') as f:
            json.dump({
                'target': target,
                'top_n': [{'path': r['path'], 'score': r['score'], 'info': r.get('info')} for r in top],
            }, f, ensure_ascii=False, indent=2)
        print(f"[保存] {args.out_json}", file=sys.stderr)

    if args.cleanup:
        top_paths = {r['path'] for r in top}
        for p in paths:
            if p not in top_paths and os.path.exists(p):
                os.remove(p)
                print(f"[清理] 删除: {p}", file=sys.stderr)

    # 输出 JSON 到 stdout
    print(json.dumps([{'path': r['path'], 'score': r['score']} for r in top], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()