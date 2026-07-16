#!/usr/bin/env python3
"""
HLZD-D3可视化 - HTML 模板生成（自包含 + D3.js CDN）
"""

import argparse
import os
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

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("[错误] jinja2 未安装，运行: pip install jinja2", file=sys.stderr)
    sys.exit(1)


SCRIPT_DIR = Path(__file__).parent
SKILL_ROOT = SCRIPT_DIR.parent
PRESETS_DIR = SKILL_ROOT / 'presets'


def _read_preset(filename):
    """读取 preset JS 文件"""
    path = PRESETS_DIR / filename
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8')


def build_html(chart_type, data, options=None):
    """
    生成自包含 HTML（含 D3.js CDN + HLZD 预设 + 数据）

    Args:
        chart_type: funnel/dashboard/geo/bar/line/pie/heatmap
        data: 图表数据
        options: {title, language, ...}

    Returns:
        HTML 字符串
    """
    options = options or {}

    # 加载所有 preset JS（按依赖顺序）
    presets_to_load = [
        ('colors.js', 'HLZD_COLORS'),
        ('utils.js', 'HLZDChart'),
        ('common/bar.js', 'HLZD_BAR'),
        ('common/line.js', 'HLZD_LINE'),
        ('common/pie.js', 'HLZD_PIE'),
        ('common/heatmap.js', 'HLZD_HEATMAP'),
        ('hlzd/funnel.js', 'HLZD_FUNNEL'),
        ('hlzd/dashboard-quote.js', 'HLZD_DASHBOARD_QUOTE'),
        ('hlzd/geo-customers.js', 'HLZD_GEO'),
    ]
    preset_scripts = '\n'.join(_read_preset(f) for f, _ in presets_to_load)

    # CDN URL（可配置）
    d3_cdn = os.environ.get('D3_CDN_URL', 'https://d3js.org/d3.v7.min.js')
    topo_cdn = os.environ.get('TOPOJSON_CDN_URL', 'https://d3js.org/topojson.v3.min.js')

    # 根据 chart_type 选渲染函数
    render_map = {
        'funnel': 'HLZD_FUNNEL.draw("{container}", {data})',
        'dashboard': 'HLZD_DASHBOARD_QUOTE.draw("{container}", {data})',
        'geo': 'HLZD_GEO.draw("{container}", {data})',
        'bar': 'HLZD_BAR.draw("{container}", {data})',
        'line': 'HLZD_LINE.draw("{container}", {data})',
        'pie': 'HLZD_PIE.draw("{container}", {data})',
        'heatmap': 'HLZD_HEATMAP.draw("{container}", {data})',
    }
    render_call = render_map.get(chart_type, 'console.error("未知 chart_type: ' + chart_type + '")')
    render_call = render_call.format(container='chart-container', data='chartData')

    title = options.get('title', f'HLZD {chart_type.upper()}')

    # 用占位符 + replace 避免 f-string 与 JS 模板冲突
    data_placeholder = '___HLZD_DATA_PLACEHOLDER___'
    render_call_placeholder = '___HLZD_RENDER_CALL___'

    html = """<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="UTF-8">
<title>__TITLE__</title>
<script src="__D3_CDN__"></script>
<script src="__TOPO_CDN__"></script>
<style>
  body { margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #FAFAFA; }
  h1 { color: #262626; margin: 0 0 20px 0; }
  #chart-container { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
  .hlzd-tooltip { position: absolute; visibility: hidden; background: white; border: 1px solid #E8E8E8; padding: 8px 12px; border-radius: 4px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); pointer-events: none; z-index: 1000; }
</style>
</head>
<body>
<h1>__TITLE__</h1>
<div id="chart-container"></div>
<script>
__PRESETS__

// 图表数据
const chartData = __DATA_PLACEHOLDER__;

// 渲染
__RENDER_CALL__
</script>
</body>
</html>"""

    import json
    html = (html
            .replace('__LANG__', options.get('language', 'zh-CN').replace('_', '-'))
            .replace('__TITLE__', title)
            .replace('__D3_CDN__', d3_cdn)
            .replace('__TOPO_CDN__', topo_cdn)
            .replace('__PRESETS__', preset_scripts)
            .replace('__DATA_PLACEHOLDER__', json.dumps(data, ensure_ascii=False))
            .replace('__RENDER_CALL__', render_call))

    return html


def main():
    parser = argparse.ArgumentParser(description='HLZD-D3 HTML 模板生成')
    parser.add_argument('--chart-type', required=True,
                        choices=['funnel', 'dashboard', 'geo', 'bar', 'line', 'pie', 'heatmap'])
    parser.add_argument('--data-file', required=True, help='数据 JSON 路径')
    parser.add_argument('--output', required=True, help='输出 HTML 路径')
    parser.add_argument('--title', help='图表标题')
    parser.add_argument('--language', default='zh-CN', help='HTML lang')
    args = parser.parse_args()

    import json
    with open(args.data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    html = build_html(args.chart_type, data, {
        'title': args.title or f'HLZD {args.chart_type.upper()}',
        'language': args.language
    })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[完成] {args.output} ({len(html)} bytes)")


if __name__ == '__main__':
    main()