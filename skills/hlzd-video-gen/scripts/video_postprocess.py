#!/usr/bin/env python3
"""
HLZD-视频生成 - 视频后处理模块
职责：
  1. 多段视频拼接（突破18秒硬上限）
  2. BGM 自动混音
  3. 字幕烧录（FFmpeg drawtext）
  4. 输出最终 MP4

依赖：FFmpeg 必须安装并在 PATH 中
"""

import argparse
import json
import os
import subprocess
import sys
import warnings

warnings.filterwarnings('ignore')

# Windows UTF-8 兼容（Python 3.7+ 默认 UTF-8，无需 wrapper）


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
BGM_DIR = os.path.join(SKILL_ROOT, 'assets', 'bgm')


# ============ FFmpeg 路径 ============
def get_ffmpeg_path():
    """获取 ffmpeg 路径"""
    ffmpeg = os.environ.get('FFMPEG_PATH', 'ffmpeg')
    if os.path.isabs(ffmpeg) and os.path.exists(ffmpeg):
        return ffmpeg
    # PATH 查找
    import shutil
    found = shutil.which(ffmpeg) or shutil.which('ffmpeg.exe')
    if not found:
        print("[错误] FFmpeg 未安装或不在 PATH 中", file=sys.stderr)
        print("  下载: https://ffmpeg.org/download.html", file=sys.stderr)
        sys.exit(1)
    return found


# ============ 多段拼接 ============
def concat_videos(video_paths, output_path, transition='fade', transition_duration=0.5):
    """
    拼接多段视频（带过渡）
    video_paths: list of str
    output_path: str
    transition: 'none' / 'fade'（黑场过渡）
    transition_duration: 过渡时长（秒）

    Strategy:
      1. 先用 concat demuxer 拼接（最快）
      2. 如需过渡，用 filter_complex + xfade
    """
    ffmpeg = get_ffmpeg_path()

    if transition == 'none' or len(video_paths) == 1:
        # 简单 concat
        list_file = output_path + '.list.txt'
        with open(list_file, 'w', encoding='utf-8') as f:
            for p in video_paths:
                # FFmpeg concat demuxer 要求绝对路径且无单引号
                p_clean = p.replace("'", "'\\''")
                f.write(f"file '{p_clean}'\n")

        cmd = [
            ffmpeg, '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_path
        ]
        _run_ffmpeg(cmd)
        os.remove(list_file)
        return output_path

    # 带过渡：需要先 normalize 到统一规格，再用 xfade
    # 简化版：统一 1280x720 24fps + xfade fade
    target_w, target_h = 1280, 720
    target_fps = 24

    inputs = []
    for p in video_paths:
        inputs.extend(['-i', p])

    # 计算每个 xfade offset
    # 假设每段都是同样长度（按 len(video_paths) 平均分配）
    n = len(video_paths)
    # 先获取每段时长
    durations = [_probe_duration(p) for p in video_paths]
    print(f"[拼接] {n} 段，每段时长: {[f'{d:.1f}s' for d in durations]}", file=sys.stderr)

    # 简化：每段先 scale+pad 到统一规格，再依次 xfade
    filter_parts = []
    for i in range(n):
        filter_parts.append(
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,fps={target_fps}[v{i}]"
        )

    # 累积 xfade
    if n == 2:
        offset = max(0, durations[0] - transition_duration)
        filter_parts.append(
            f"[v0][v1]xfade=transition=fade:duration={transition_duration}:offset={offset}[vout]"
        )
    else:
        # 多段：累积拼接
        prev = 'v0'
        cum_offset = durations[0]
        for i in range(1, n):
            out_label = f'vtmp{i}' if i < n - 1 else 'vout'
            offset = max(0, cum_offset - transition_duration)
            filter_parts.append(
                f"[{prev}][v{i}]xfade=transition=fade:duration={transition_duration}:offset={offset}[{out_label}]"
            )
            cum_offset += durations[i] - transition_duration
            prev = out_label

    filter_complex = ';'.join(filter_parts)

    cmd = [
        ffmpeg, '-y',
        *inputs,
        '-filter_complex', filter_complex,
        '-map', '[vout]',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        output_path
    ]
    _run_ffmpeg(cmd)
    return output_path


def _probe_duration(path):
    """用 ffprobe 获取视频时长（秒）"""
    import shutil
    ffprobe = shutil.which('ffprobe') or shutil.which('ffprobe.exe')
    if not ffprobe:
        return 10.0  # fallback
    try:
        result = subprocess.run(
            [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 10.0


# ============ BGM 合成 ============
def get_bgm_path(style='corporate'):
    """获取 BGM 文件路径"""
    candidates = [
        os.path.join(BGM_DIR, f'{style}.mp3'),
        os.path.join(BGM_DIR, f'{style}.wav'),
        os.path.join(BGM_DIR, f'{style}.ogg'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def add_bgm(video_path, bgm_path, output_path, original_volume=0.1, bgm_volume=0.3):
    """
    给视频添加 BGM
    original_volume: 原声音量（0-1）
    bgm_volume: BGM 音量（0-1）
    """
    ffmpeg = get_ffmpeg_path()

    if not bgm_path or not os.path.exists(bgm_path):
        print(f"[警告] BGM 不存在: {bgm_path}，跳过添加", file=sys.stderr)
        # 直接复制
        import shutil
        shutil.copy(video_path, output_path)
        return output_path

    # 获取视频时长
    duration = _probe_duration(video_path)

    # BGM loop 到视频时长
    cmd = [
        ffmpeg, '-y',
        '-i', video_path,
        '-stream_loop', '-1', '-i', bgm_path,
        '-filter_complex',
        f'[0:a]volume={original_volume}[a0];'
        f'[1:a]volume={bgm_volume},atrim=0:{duration}[a1];'
        f'[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]',
        '-map', '0:v',
        '-map', '[aout]',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ]
    _run_ffmpeg(cmd)
    return output_path


# ============ 字幕烧录 ============
def burn_subtitles(video_path, subtitles, output_path, lang='en'):
    """
    把字幕烧录到视频
    subtitles: list of {text, start, end}
    lang: 'en' / 'zh' / 'bilingual'
    """
    ffmpeg = get_ffmpeg_path()

    if not subtitles:
        import shutil
        shutil.copy(video_path, output_path)
        return output_path

    # 动态 import 避免循环
    sys.path.insert(0, SCRIPT_DIR)
    from subtitle_manager import build_drawtext_filters
    filters = build_drawtext_filters(subtitles, lang=lang)

    filter_str = ','.join(filters)

    cmd = [
        ffmpeg, '-y',
        '-i', video_path,
        '-vf', filter_str,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        output_path
    ]
    _run_ffmpeg(cmd)
    return output_path


# ============ 一站式：拼接 + BGM + 字幕 ============
def finalize_video(segments, output_path, bgm_style='corporate', subtitles=None,
                   subtitle_lang='en', transition='fade'):
    """
    完整后处理流程
    segments: list of str（已生成的视频片段路径）
    output_path: 最终输出路径
    bgm_style: BGM 风格（corporate / industrial / upbeat / epic / none）
    subtitles: 字幕列表（None=不烧字幕）
    subtitle_lang: 字幕语言
    transition: 段间过渡
    """
    # 1. 拼接
    if len(segments) > 1:
        merged = output_path.replace('.mp4', '_merged.mp4')
        concat_videos(segments, merged, transition=transition)
    else:
        merged = segments[0]

    # 2. BGM
    if bgm_style and bgm_style != 'none':
        bgm_added = output_path.replace('.mp4', '_bgm.mp4')
        bgm_path = get_bgm_path(bgm_style)
        add_bgm(merged, bgm_path, bgm_added)
    else:
        bgm_added = merged

    # 3. 字幕
    if subtitles:
        burn_subtitles(bgm_added, subtitles, output_path, lang=subtitle_lang)
    else:
        # 直接重命名
        if bgm_added != output_path:
            import shutil
            shutil.move(bgm_added, output_path)

    # 清理中间文件
    for tmp in [merged, bgm_added]:
        if os.path.exists(tmp) and tmp != output_path:
            try:
                os.remove(tmp)
            except OSError:
                pass

    return output_path


# ============ FFmpeg 工具 ============
def _run_ffmpeg(cmd):
    """运行 ffmpeg 命令，统一错误处理"""
    print(f"[FFmpeg] {' '.join(cmd[:6])}...", file=sys.stderr)
    # Windows 下 FFmpeg 输出可能含中文（drawtext 字幕），强制 UTF-8 解码 + 容错
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    if result.returncode != 0:
        stderr_text = result.stderr or ""
        print(f"[FFmpeg 错误]\n{stderr_text[-1000:]}", file=sys.stderr)
        sys.exit(1)
    print(f"[FFmpeg] 完成", file=sys.stderr)


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='视频后处理')
    parser.add_argument('--segments', nargs='+', help='视频片段路径（空格分隔）')
    parser.add_argument('--output', required=True, help='最终输出 MP4 路径')
    parser.add_argument('--bgm-style', default='corporate', choices=['corporate', 'industrial', 'upbeat', 'epic', 'none'])
    parser.add_argument('--subtitles-json', help='字幕 JSON 文件路径（subtitle_manager.py 输出）')
    parser.add_argument('--subtitle-lang', default='en', choices=['en', 'zh', 'bilingual'])
    parser.add_argument('--transition', default='fade', choices=['none', 'fade'])
    args = parser.parse_args()

    if not args.segments:
        print("[错误] 需要 --segments", file=sys.stderr)
        sys.exit(1)

    subtitles = None
    if args.subtitles_json and os.path.exists(args.subtitles_json):
        with open(args.subtitles_json, 'r', encoding='utf-8') as f:
            subtitles = json.load(f).get('subtitles', [])

    result = finalize_video(
        segments=args.segments,
        output_path=args.output,
        bgm_style=args.bgm_style,
        subtitles=subtitles,
        subtitle_lang=args.subtitle_lang,
        transition=args.transition,
    )
    print(f"[完成] {result}")


if __name__ == '__main__':
    main()