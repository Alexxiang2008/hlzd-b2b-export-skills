#!/usr/bin/env python3
"""
HLZD-视频生成 - 字幕管理器
负责：
  1. 从 i18n_catalog.yaml 加载中英对照
  2. 根据产品类别 + 语言生成字幕序列
  3. 渲染为 FFmpeg drawtext 过滤器字符串

设计原则：默认输出英文（出海），中文作为对照保留
"""

import argparse
import json
import os
import sys
import warnings

warnings.filterwarnings('ignore')

# Windows UTF-8 兼容（Python 3.7+ 默认 UTF-8，无需 wrapper）

try:
    import yaml
except ImportError:
    print("[错误] PyYAML 未安装", file=sys.stderr)
    sys.exit(1)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
CATALOG_PATH = os.path.join(SKILL_ROOT, 'presets', 'subtitles', 'i18n_catalog.yaml')
FONTS_DIR = os.path.join(SKILL_ROOT, 'assets', 'fonts')


# ============ 字体路径 ============
def get_font_path(lang='en'):
    """
    根据语言选择字体（解决中文字体问题）
    lang: 'en' / 'zh' / 'bilingual'
    Returns: 字体文件路径（不存在时返回 None，FFmpeg 会用系统默认）
    """
    # 双语/中文：用思源黑体（开源免费）
    if lang in ('zh', 'bilingual'):
        font_candidates = [
            os.path.join(FONTS_DIR, 'SourceHanSans-Regular.ttf'),
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
        ]
    else:
        # 英文：用阿里巴巴普惠体（开源免费）
        font_candidates = [
            os.path.join(FONTS_DIR, 'AlibabaPuHuiTi-Regular.ttf'),
            'C:/Windows/Fonts/arial.ttf',
        ]

    for fp in font_candidates:
        if os.path.exists(fp):
            # FFmpeg filter 语法中冒号(:)是分隔符，必须转义为 \:
            # 同时 Windows 路径用正斜杠 FFmpeg 也支持
            escaped = fp.replace('\\', '/').replace(':', '\\:')
            return escaped
    return None


# ============ 字幕加载 ============
def load_catalog():
    """加载字幕对照表"""
    if not os.path.exists(CATALOG_PATH):
        print(f"[警告] 字幕对照表不存在: {CATALOG_PATH}", file=sys.stderr)
        return {}
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# ============ 字幕生成 ============
def generate_subtitles(product_key, lang='en', max_tags=3):
    """
    根据产品 key 生成字幕序列
    product_key: 产品在 i18n_catalog.yaml 中的 key（如 'oil_casing'）
    lang: 'en' / 'zh' / 'bilingual'
    max_tags: 最多展示几个标签

    Returns: list of {text, start_time, end_time}
      - 第 1 条：产品名（开场 1.5s）
      - 第 2-4 条：标签（每个 2s）
    """
    catalog = load_catalog()
    product_entry = catalog.get('products', {}).get(product_key, {})

    name_entry = product_entry.get('name', {})
    tags = product_entry.get('tags', [])

    if not name_entry:
        return []

    subtitles = []
    t = 0.0

    # 第 1 条：产品名（1.5 秒）
    if lang == 'bilingual':
        text = f"{name_entry.get('en', '')} | {name_entry.get('zh', '')}"
    elif lang == 'zh':
        text = name_entry.get('zh', name_entry.get('en', ''))
    else:
        text = name_entry.get('en', name_entry.get('zh', ''))

    subtitles.append({'text': text, 'start': t, 'end': t + 1.5})
    t += 1.5

    # 第 2-N 条：标签（每个 2 秒）
    for tag in tags[:max_tags]:
        if lang == 'bilingual':
            text = f"{tag.get('en', '')} | {tag.get('zh', '')}"
        elif lang == 'zh':
            text = tag.get('zh', tag.get('en', ''))
        else:
            text = tag.get('en', tag.get('zh', ''))

        subtitles.append({'text': text, 'start': t, 'end': t + 2.0})
        t += 2.0

    return subtitles


def generate_custom_subtitles(text_lines, duration):
    """
    自定义字幕（用户直接传入文本行）
    text_lines: list of str
    duration: 总时长（秒）

    Returns: list of {text, start, end}（均匀分配时间）
    """
    if not text_lines:
        return []
    n = len(text_lines)
    each = duration / n
    return [
        {'text': text_lines[i], 'start': i * each, 'end': (i + 1) * each}
        for i in range(n)
    ]


# ============ FFmpeg drawtext 过滤器 ============
def build_drawtext_filters(subtitles, lang='en', font_size=36, color='white',
                           box_color='black@0.5', margin_v=60):
    """
    生成 FFmpeg drawtext 过滤器列表
    subtitles: list of {text, start, end}
    lang: 'en' / 'zh' / 'bilingual'

    Returns: list of filter strings（可直接传入 ffmpeg -filter_complex）
    """
    font_path = get_font_path(lang)
    filters = []

    for sub in subtitles:
        text = sub['text']
        # FFmpeg drawtext 需要转义单引号/冒号/反斜杠/百分号
        text_escaped = (
            text.replace('\\', '\\\\')
                .replace(':', '\\:')
                .replace("'", "\\'")
                .replace('%', '\\%')
        )

        parts = [
            f"drawtext=",
            f"text='{text_escaped}'",
        ]

        if font_path:
            parts.append(f"fontfile='{font_path}'")
        parts.append(f"fontsize={font_size}")
        parts.append(f"fontcolor={color}")
        parts.append(f"box=1")
        parts.append(f"boxcolor={box_color}")
        parts.append(f"boxborderw=8")
        parts.append(f"x=(w-text_w)/2")
        parts.append(f"y=h-th-{margin_v}")
        parts.append(f"enable='between(t,{sub['start']},{sub['end']})'")

        filters.append(':'.join(parts))

    return filters


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='字幕管理器')
    parser.add_argument('--product-key', help='产品 key（如 oil_casing）')
    parser.add_argument('--lang', default='en', choices=['en', 'zh', 'bilingual'])
    parser.add_argument('--custom-text', help='自定义字幕，\\n 分隔多行')
    parser.add_argument('--duration', type=float, help='自定义字幕总时长（秒）')
    parser.add_argument('--max-tags', type=int, default=3, help='最多展示标签数')
    parser.add_argument('--out', help='输出 JSON 路径')
    args = parser.parse_args()

    if args.custom_text:
        text_lines = [line.strip() for line in args.custom_text.split('\\n') if line.strip()]
        subtitles = generate_custom_subtitles(text_lines, args.duration or len(text_lines) * 2.0)
    elif args.product_key:
        subtitles = generate_subtitles(args.product_key, args.lang, args.max_tags)
    else:
        print("[错误] 需要 --product-key 或 --custom-text", file=sys.stderr)
        sys.exit(1)

    # 输出
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump({'lang': args.lang, 'subtitles': subtitles}, f, ensure_ascii=False, indent=2)
        print(f"[保存] {args.out}")
    else:
        print(json.dumps({'lang': args.lang, 'subtitles': subtitles}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()