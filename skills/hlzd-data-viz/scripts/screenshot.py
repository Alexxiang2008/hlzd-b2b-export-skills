#!/usr/bin/env python3
"""
HLZD-D3可视化 - HTML → PNG 截图（可选，用 Playwright）
用于嵌入 HLZD-办公文档 PDF
"""

import argparse
import sys
import io
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')


def _ensure_utf8_stdio():
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


def screenshot_html(html_path, png_path, viewport_width=1024, viewport_height=768):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[错误] playwright 未安装，运行: pip install playwright", file=sys.stderr)
        print("  然后: playwright install chromium", file=sys.stderr)
        sys.exit(1)

    html_path = Path(html_path).absolute()
    png_path = Path(png_path).absolute()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': viewport_width, 'height': viewport_height})
        page = context.new_page()
        page.goto(f'file://{html_path}')
        page.wait_for_timeout(2000)  # 等 D3.js 渲染

        page.screenshot(path=str(png_path), full_page=True)
        browser.close()

    print(f"[完成] {png_path}")


def main():
    parser = argparse.ArgumentParser(description='HLZD-D3 HTML → PNG 截图')
    parser.add_argument('--input', required=True, help='输入 HTML')
    parser.add_argument('--output', required=True, help='输出 PNG')
    parser.add_argument('--width', type=int, default=1024, help='视口宽度')
    parser.add_argument('--height', type=int, default=768, help='视口高度')
    args = parser.parse_args()

    screenshot_html(args.input, args.output, args.width, args.height)


if __name__ == '__main__':
    main()