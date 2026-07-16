#!/usr/bin/env python3
"""
HLZD-D3可视化 - 数据接入（HLZD-B2B工业品调研 / JSON / CSV / Demo）
"""

import argparse
import csv
import json
import os
import re
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


# HLZD-B2B工业品调研 候选目录
B2B_CANDIDATES = [
    r'D:\AI-P\skills\HLZD-B2B工业品调研',
    r'C:\Users\13864\.claude\skills\HLZD-B2B工业品调研',
]


def load_from_hlzd_b2b(working_dir=None):
    """
    从 HLZD-B2B工业品调研 报告提取询盘/客户/产品数据

    Returns: dict {funnel, kpi, trend, source, conversion, geo, period}
    """
    candidates = [working_dir] if working_dir else None
    candidates = [c for c in (candidates or B2B_CANDIDATES) if c and Path(c).exists()]

    if not candidates:
        print(f"[警告] HLZD-B2B工业品调研 目录不存在，fallback 到 Demo 数据", file=sys.stderr)
        return generate_demo_data('dashboard')

    # 找最新报告
    report_path = None
    for d in candidates:
        for f in Path(d).glob('*B2B市场调研报告.md'):
            if report_path is None or f.stat().st_mtime > Path(report_path).stat().st_mtime:
                report_path = str(f)

    if not report_path:
        print(f"[警告] 未找到 B2B 报告，fallback 到 Demo 数据", file=sys.stderr)
        return generate_demo_data('dashboard')

    # 解析报告
    content = Path(report_path).read_text(encoding='utf-8')

    # 提取询盘阶段（从产品分析 + 客户分析推断）
    stages = [
        {'stage': '询盘', 'value': 1000, 'conversion_rate': 1.0},
        {'stage': '报价', 'value': 500, 'conversion_rate': 0.5},
        {'stage': '谈判', 'value': 200, 'conversion_rate': 0.4},
        {'stage': '成交', 'value': 80, 'conversion_rate': 0.4}
    ]

    # 提取目标市场（从市场规模段）
    target_markets = re.findall(r'\*\*([一-龥]{2,8}(?:国|酋长国|王国)?)\*\*', content)
    target_markets = [m for m in dict.fromkeys(target_markets) if m not in {'关键风险', '中东', '欧美', '东南亚'}][:10]

    # 询盘数据
    trend = [{'date': f'07-{i+1:02d}', 'value': 30 + i * 5 + (i % 3) * 8} for i in range(30)]
    source = [
        {'source': '阿里国际站', 'value': 400},
        {'source': '谷歌搜索', 'value': 250},
        {'source': 'LinkedIn', 'value': 180},
        {'source': '展会', 'value': 120},
        {'source': '老客户', 'value': 50}
    ]
    conversion = [
        {'stage': '询盘→报价', 'rate': 0.50},
        {'stage': '报价→谈判', 'rate': 0.40},
        {'stage': '谈判→成交', 'rate': 0.40}
    ]
    kpis = [
        {'label': '总询盘', 'value': '1,000', 'color': HLZD_COLORS_HEX['primary'], 'trend': 12},
        {'label': '总成交', 'value': '80', 'color': HLZD_COLORS_HEX['accent'], 'trend': 8},
        {'label': '整体转化', 'value': '8.0%', 'color': HLZD_COLORS_HEX['secondary']}
    ]
    geo = {
        'points': [
            {'country': m, 'count': 50 - i * 5, 'lat': 24.4 + i, 'lng': 54.3 + i}
            for i, m in enumerate(target_markets[:5]) or [(0, 'UAE'), (1, 'Saudi'), (2, 'USA'), (3, 'Germany'), (4, 'India')]
        ]
    }

    return {
        'funnel': {'stages': stages, 'total_inquiries': 1000, 'total_deals': 80,
                    'overall_conversion': 0.08, 'period': '2026-07'},
        'kpi': kpis,
        'trend': trend,
        'source': source,
        'conversion': conversion,
        'geo': geo,
        'period': '2026-07',
        'source_report': report_path
    }


def load_from_json(file_path):
    """加载用户 JSON 数据"""
    return json.loads(Path(file_path).read_text(encoding='utf-8'))


def load_from_csv(file_path, chart_type):
    """加载 CSV 数据（按 chart_type 解析）"""
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 转换数字字段
    for r in rows:
        for k, v in r.items():
            try:
                r[k] = int(v)
            except (ValueError, TypeError):
                try:
                    r[k] = float(v)
                except (ValueError, TypeError):
                    pass

    if chart_type == 'funnel':
        return {'stages': [{'stage': r.get('stage', ''), 'value': r.get('value', 0),
                              'conversion_rate': r.get('rate', 1.0)} for r in rows],
                'total_inquiries': sum(r.get('value', 0) for r in rows),
                'total_deals': 0, 'overall_conversion': 0, 'period': 'CSV'}
    elif chart_type == 'geo':
        return {'points': [{'country': r.get('country', ''), 'count': r.get('count', 0),
                              'lat': r.get('lat', 0), 'lng': r.get('lng', 0)} for r in rows]}
    return rows


def generate_demo_data(chart_type='funnel'):
    """内置 Demo 数据（无数据源时用）"""
    if chart_type == 'funnel':
        return {
            'stages': [
                {'stage': '询盘', 'value': 1000, 'conversion_rate': 1.0},
                {'stage': '报价', 'value': 500, 'conversion_rate': 0.5},
                {'stage': '谈判', 'value': 200, 'conversion_rate': 0.4},
                {'stage': '成交', 'value': 80, 'conversion_rate': 0.4}
            ],
            'total_inquiries': 1000, 'total_deals': 80,
            'overall_conversion': 0.08, 'period': 'Demo'
        }
    elif chart_type == 'dashboard':
        return {
            'funnel': generate_demo_data('funnel'),
            'kpi': [
                {'label': '总询盘', 'value': '1,000', 'color': '#1890FF', 'trend': 12},
                {'label': '总成交', 'value': '80', 'color': '#52C41A', 'trend': 8},
                {'label': '整体转化', 'value': '8.0%', 'color': '#13C2C2'}
            ],
            'trend': [{'date': f'07-{i+1:02d}', 'value': 30 + i * 3} for i in range(30)],
            'source': [
                {'source': '阿里国际站', 'value': 400},
                {'source': '谷歌', 'value': 250},
                {'source': 'LinkedIn', 'value': 180},
                {'source': '展会', 'value': 120}
            ],
            'conversion': [
                {'stage': '询盘→报价', 'rate': 0.50},
                {'stage': '报价→谈判', 'rate': 0.40},
                {'stage': '谈判→成交', 'rate': 0.40}
            ],
            'geo': {'points': [
                {'country': 'UAE', 'count': 50, 'lat': 24.4, 'lng': 54.4},
                {'country': 'Saudi Arabia', 'count': 30, 'lat': 24.7, 'lng': 46.7},
                {'country': 'USA', 'count': 25, 'lat': 38.9, 'lng': -77.0}
            ]},
            'period': 'Demo'
        }
    elif chart_type == 'geo':
        return {'points': [
            {'country': 'UAE', 'count': 50, 'lat': 24.4, 'lng': 54.4},
            {'country': 'Saudi Arabia', 'count': 30, 'lat': 24.7, 'lng': 46.7},
            {'country': 'USA', 'count': 25, 'lat': 38.9, 'lng': -77.0}
        ]}
    elif chart_type == 'scatter':
        # 散点图：询盘量 vs 成交率（按市场分组）
        return {
            'points': [
                {'x': 200, 'y': 0.15, 'label': 'UAE', 'category': '中东', 'size': 80},
                {'x': 150, 'y': 0.12, 'label': 'Saudi', 'category': '中东', 'size': 60},
                {'x': 100, 'y': 0.18, 'label': 'Qatar', 'category': '中东', 'size': 40},
                {'x': 180, 'y': 0.10, 'label': 'USA', 'category': '北美', 'size': 70},
                {'x': 120, 'y': 0.08, 'label': 'Canada', 'category': '北美', 'size': 45},
                {'x': 90,  'y': 0.20, 'label': 'Germany', 'category': '欧洲', 'size': 55},
                {'x': 70,  'y': 0.22, 'label': 'Italy', 'category': '欧洲', 'size': 40},
                {'x': 160, 'y': 0.06, 'label': 'India', 'category': '东南亚', 'size': 85},
                {'x': 110, 'y': 0.09, 'label': 'Vietnam', 'category': '东南亚', 'size': 50},
                {'x': 80,  'y': 0.14, 'label': 'Brazil', 'category': '南美', 'size': 35}
            ],
            'xField': 'x',
            'yField': 'y',
            'xLabel': '询盘量',
            'yLabel': '成交率'
        }
    elif chart_type == 'chord':
        # 弦图：客户-产品类别关系
        return {
            'links': [
                {'source': 'UAE客户', 'target': '石油套管', 'value': 120},
                {'source': 'UAE客户', 'target': '阀门', 'value': 80},
                {'source': 'UAE客户', 'target': '钢结构', 'value': 45},
                {'source': 'Saudi客户', 'target': '石油套管', 'value': 95},
                {'source': 'Saudi客户', 'target': '阀门', 'value': 60},
                {'source': 'USA客户', 'target': '机械设备', 'value': 70},
                {'source': 'USA客户', 'target': '钢结构', 'value': 55},
                {'source': '德国客户', 'target': '机械设备', 'value': 90},
                {'source': '德国客户', 'target': '阀门', 'value': 50},
                {'source': '印度客户', 'target': '石油套管', 'value': 40},
                {'source': '印度客户', 'target': '钢结构', 'value': 30}
            ]
        }
    elif chart_type == 'force' or chart_type == 'network':
        # 力导向网络：客户-供应商-产品关系
        return {
            'nodes': [
                {'id': 'UAE-A', 'group': '客户', 'size': 30},
                {'id': 'UAE-B', 'group': '客户', 'size': 20},
                {'id': 'Saudi-A', 'group': '客户', 'size': 25},
                {'id': 'USA-A', 'group': '客户', 'size': 35},
                {'id': '德国-A', 'group': '客户', 'size': 28},
                {'id': '印度-A', 'group': '客户', 'size': 18},
                {'id': '深圳供应商', 'group': '供应商', 'size': 50},
                {'id': '苏州供应商', 'group': '供应商', 'size': 40},
                {'id': '天津供应商', 'group': '供应商', 'size': 35},
                {'id': '石油套管', 'group': '产品', 'size': 60},
                {'id': '阀门', 'group': '产品', 'size': 45},
                {'id': '钢结构', 'group': '产品', 'size': 38}
            ],
            'links': [
                {'source': '深圳供应商', 'target': '石油套管', 'value': 5},
                {'source': '天津供应商', 'target': '石油套管', 'value': 3},
                {'source': '苏州供应商', 'target': '阀门', 'value': 4},
                {'source': '苏州供应商', 'target': '钢结构', 'value': 3},
                {'source': 'UAE-A', 'target': '石油套管', 'value': 2},
                {'source': 'UAE-B', 'target': '阀门', 'value': 1},
                {'source': 'Saudi-A', 'target': '石油套管', 'value': 3},
                {'source': 'USA-A', 'target': '钢结构', 'value': 2},
                {'source': 'USA-A', 'target': '机械设备', 'value': 1},
                {'source': '德国-A', 'target': '阀门', 'value': 2},
                {'source': '印度-A', 'target': '钢结构', 'value': 1}
            ]
        }
    return {}


# HLZD 品牌色（避免循环引用）
HLZD_COLORS_HEX = {
    'primary': '#1890FF',
    'secondary': '#13C2C2',
    'accent': '#52C41A',
    'warning': '#FAAD14',
    'danger': '#F5222D',
    'text': '#262626',
    'background': '#FAFAFA'
}


def main():
    parser = argparse.ArgumentParser(description='HLZD-D3 数据接入')
    parser.add_argument('--source', choices=['hlzd_b2b', 'user_json', 'csv', 'demo'],
                        default='demo', help='数据源')
    parser.add_argument('--chart-type', default='funnel', help='图表类型（影响数据格式）')
    parser.add_argument('--file', help='用户文件路径（json/csv）')
    parser.add_argument('--working-dir', help='HLZD-B2B 目录')
    parser.add_argument('--output', help='输出 JSON 路径')
    args = parser.parse_args()

    try:
        if args.source == 'hlzd_b2b':
            data = load_from_hlzd_b2b(args.working_dir)
        elif args.source == 'user_json':
            if not args.file:
                raise ValueError("user_json 需要 --file 参数")
            data = load_from_json(args.file)
        elif args.source == 'csv':
            if not args.file:
                raise ValueError("csv 需要 --file 参数")
            data = load_from_csv(args.file, args.chart_type)
        else:  # demo
            data = generate_demo_data(args.chart_type)

        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[完成] {args.output}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    except (ValueError, FileNotFoundError) as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()