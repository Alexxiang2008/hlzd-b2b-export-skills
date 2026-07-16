#!/usr/bin/env python3
"""
HLZD-D3可视化 - 主调度（SKILL.md 实际调用入口）
"""

import argparse
import json
import os
import sys
import io
import time
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


SCRIPT_DIR = Path(__file__).parent


def run_chart(chart_type, data, options=None):
    """统一图表路由"""
    from html_builder import build_html
    from output_manager import save_history_entry

    options = options or {}
    html = build_html(chart_type, data, options)

    # 临时文件 + 复制到 outputs
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        tmp_path = f.name

    from output_manager import save_html
    chart_title = options.get('title', chart_type)
    customer = options.get('customer', 'demo')
    suggested_name = f"{chart_type}_{customer}_{time.strftime('%Y%m%d')}.html"
    output_path = save_html(html, suggested_name)

    # 写历史
    meta = {
        'chart_type': chart_type,
        'data_source': options.get('data_source', 'demo'),
        'language': options.get('language', 'zh_CN'),
        'cost': 0.0,
        'params': options
    }
    save_history_entry(meta, output_path)

    return {'output_file': output_path, 'meta': meta}


def run_funnel(data, options):
    return run_chart('funnel', data, options)


def run_dashboard(data, options):
    return run_chart('dashboard', data, options)


def run_geo(data, options):
    return run_chart('geo', data, options)


def run_scatter(data, options):
    return run_chart('scatter', data, options)


def run_chord(data, options):
    return run_chart('chord', data, options)


def run_force(data, options):
    return run_chart('force', data, options)


def run_b2b_loop(args):
    """B2B 闭环：自动检测 HLZD-B2B 报告 → 解析 → 生成"""
    from data_loader import load_from_hlzd_b2b

    print("[Orchestrator] B2B 闭环：检测 HLZD-B2B工业品调研 报告...", file=sys.stderr)
    data = load_from_hlzd_b2b(args.working_dir)

    if args.chart_type == 'funnel':
        return run_funnel(data['funnel'], {
            'data_source': 'hlzd_b2b',
            'language': args.lang,
            'title': f"销售漏斗图 - {data.get('period', '')}"
        })
    elif args.chart_type == 'dashboard':
        return run_dashboard(data, {
            'data_source': 'hlzd_b2b',
            'language': args.lang,
            'title': f"询盘分析看板 - {data.get('period', '')}"
        })
    elif args.chart_type == 'geo':
        return run_geo(data['geo'], {
            'data_source': 'hlzd_b2b',
            'language': args.lang,
            'title': '客户地理分布'
        })
    elif args.chart_type == 'scatter':
        return run_scatter(data.get('scatter') or data, {
            'data_source': 'hlzd_b2b',
            'language': args.lang,
            'title': '询盘量 vs 成交率'
        })
    elif args.chart_type == 'chord':
        return run_chord(data.get('chord') or data, {
            'data_source': 'hlzd_b2b',
            'language': args.lang,
            'title': '客户-产品关系'
        })
    elif args.chart_type == 'force':
        return run_force(data.get('force') or data, {
            'data_source': 'hlzd_b2b',
            'language': args.lang,
            'title': '客户-供应商-产品网络'
        })
    else:
        raise ValueError(f"不支持的 chart_type: {args.chart_type}")


def main():
    parser = argparse.ArgumentParser(description='HLZD-D3 主调度')
    parser.add_argument('--entities', help='entities JSON 路径')
    parser.add_argument('--chart-type', choices=['funnel', 'dashboard', 'geo', 'bar', 'line', 'pie', 'heatmap', 'scatter', 'chord', 'force'])
    parser.add_argument('--source', choices=['hlzd_b2b', 'user_json', 'csv', 'demo'], default='demo')
    parser.add_argument('--data-file', help='用户数据文件（JSON/CSV）')
    parser.add_argument('--working-dir', help='HLZD-B2B 目录')
    parser.add_argument('--lang', default='zh_CN')
    parser.add_argument('--auto-b2b', action='store_true', help='B2B 闭环模式')
    parser.add_argument('--title', help='图表标题')
    args = parser.parse_args()

    try:
        # B2B 闭环
        if args.auto_b2b:
            if not args.chart_type:
                print("[错误] --auto-b2b 需要 --chart-type", file=sys.stderr)
                sys.exit(1)
            result = run_b2b_loop(args)
            print("\n=== Orchestrator 完成（B2B 闭环）===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        # 从 entities.json 加载
        if args.entities:
            with open(args.entities, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            chart_type = entities.get('chart_type', args.chart_type)
            source = entities.get('data_source', args.source)
        else:
            entities = {}
            chart_type = args.chart_type
            source = args.source

        if not chart_type:
            print("[错误] 请指定 --chart-type 或 --entities", file=sys.stderr)
            sys.exit(1)

        # 数据接入
        from data_loader import load_from_hlzd_b2b, load_from_json, load_from_csv, generate_demo_data

        if source == 'hlzd_b2b':
            data = load_from_hlzd_b2b(args.working_dir)
            if chart_type == 'funnel':
                data = data['funnel']
            elif chart_type == 'dashboard':
                pass  # 全部数据
            elif chart_type == 'geo':
                data = data['geo']
        elif source == 'user_json':
            if not args.data_file:
                print("[错误] user_json 需要 --data-file", file=sys.stderr)
                sys.exit(1)
            data = load_from_json(args.data_file)
        elif source == 'csv':
            if not args.data_file:
                print("[错误] csv 需要 --data-file", file=sys.stderr)
                sys.exit(1)
            data = load_from_csv(args.data_file, chart_type)
        else:  # demo
            data = generate_demo_data(chart_type)

        # 路由
        options = {
            'data_source': source,
            'language': args.lang,
            'title': args.title or entities.get('title') or f"HLZD {chart_type}"
        }
        result = run_chart(chart_type, data, options)

        print("\n=== Orchestrator 完成 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except (ValueError, FileNotFoundError, IOError) as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()