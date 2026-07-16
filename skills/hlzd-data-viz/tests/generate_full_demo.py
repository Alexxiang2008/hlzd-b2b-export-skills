#!/usr/bin/env python3
"""
HLZD-D3可视化 - 综合 Demo 生成器
一键生成 8+ 种图表类型的示例 HTML（用真实 HLZD 询盘场景数据）

用法:
  py tests/generate_full_demo.py
"""

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
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SKILL_ROOT / 'scripts'))

from html_builder import build_html
from output_manager import save_html, save_history_entry


# ========== 真实 HLZD 询盘场景数据 ==========
HLZD_DEMO_DATA = {
    "period": "2026-07",
    "company": "深圳市海联智达科技有限公司",

    # 1. 销售漏斗（6 阶段完整版）
    "funnel": {
        "stages": [
            {"stage": "首次联系", "value": 2400, "conversion_rate": 1.0},
            {"stage": "询盘", "value": 1200, "conversion_rate": 0.5},
            {"stage": "报价", "value": 600, "conversion_rate": 0.5},
            {"stage": "打样", "value": 280, "conversion_rate": 0.467},
            {"stage": "谈判", "value": 145, "conversion_rate": 0.518},
            {"stage": "成交", "value": 58, "conversion_rate": 0.4}
        ],
        "total_inquiries": 1200,
        "total_deals": 58,
        "overall_conversion": 0.0483,
        "period": "2026-07"
    },

    # 2. 询盘分析看板（6 图组合）
    "dashboard": {
        "funnel": None,  # 引用上面的 funnel
        "kpi": [
            {"label": "总询盘", "value": "1,200", "color": "#1890FF", "trend": 18},
            {"label": "总成交", "value": "58", "color": "#52C41A", "trend": 22},
            {"label": "整体转化", "value": "4.83%", "color": "#13C2C2"},
            {"label": "平均客单价", "value": "$28K", "color": "#FAAD14", "trend": 5}
        ],
        "trend": [
            {"date": f"07-{i+1:02d}", "value": 30 + i * 3 + (i % 4) * 5}
            for i in range(30)
        ],
        "source": [
            {"source": "阿里国际站", "value": 480},
            {"source": "谷歌 SEO", "value": 280},
            {"source": "LinkedIn", "value": 180},
            {"source": "行业展会", "value": 120},
            {"source": "老客户复购", "value": 90},
            {"source": "邮件营销", "value": 50}
        ],
        "conversion": [
            {"stage": "联系→询盘", "rate": 0.50},
            {"stage": "询盘→报价", "rate": 0.50},
            {"stage": "报价→打样", "rate": 0.467},
            {"stage": "打样→谈判", "rate": 0.518},
            {"stage": "谈判→成交", "rate": 0.40}
        ],
        "geo": None,  # 引用下面的 geo
        "period": "2026-07"
    },

    # 3. 客户地理分布（8 国 + 大洲）
    "geo": {
        "points": [
            {"country": "UAE", "region": "中东", "count": 85, "lat": 24.4539, "lng": 54.3773},
            {"country": "Saudi Arabia", "region": "中东", "count": 62, "lat": 24.7136, "lng": 46.6753},
            {"country": "Qatar", "region": "中东", "count": 28, "lat": 25.2854, "lng": 51.5310},
            {"country": "USA", "region": "北美", "count": 45, "lat": 38.9072, "lng": -77.0369},
            {"country": "Germany", "region": "欧洲", "count": 32, "lat": 52.5200, "lng": 13.4050},
            {"country": "Russia", "region": "欧亚", "count": 25, "lat": 55.7558, "lng": 37.6173},
            {"country": "India", "region": "南亚", "count": 38, "lat": 28.6139, "lng": 77.2090},
            {"country": "Brazil", "region": "南美", "count": 18, "lat": -15.7975, "lng": -47.8919}
        ]
    },

    # 4. 产品 vs 地区 热力图（新增）
    "product_region_heatmap": [
        {"row": "OCTG 套管", "column": "中东", "value": 95},
        {"row": "OCTG 套管", "column": "北美", "value": 45},
        {"row": "OCTG 套管", "column": "欧洲", "value": 25},
        {"row": "OCTG 套管", "column": "南亚", "value": 30},
        {"row": "OCTG 套管", "column": "南美", "value": 12},
        {"row": "工业阀门", "column": "中东", "value": 60},
        {"row": "工业阀门", "column": "北美", "value": 35},
        {"row": "工业阀门", "column": "欧洲", "value": 40},
        {"row": "工业阀门", "column": "南亚", "value": 18},
        {"row": "工业阀门", "column": "南美", "value": 8},
        {"row": "钢结构", "column": "中东", "value": 75},
        {"row": "钢结构", "column": "北美", "value": 20},
        {"row": "钢结构", "column": "欧洲", "value": 15},
        {"row": "钢结构", "column": "南亚", "value": 25},
        {"row": "钢结构", "column": "南美", "value": 5}
    ],

    # 5. 询盘量 vs 转化率 散点图（新增）
    "scatter": [
        {"country": "UAE", "inquiries": 85, "conversion": 0.082, "size": 85000},
        {"country": "Saudi", "inquiries": 62, "conversion": 0.065, "size": 62000},
        {"country": "USA", "inquiries": 45, "conversion": 0.044, "size": 45000},
        {"country": "Germany", "inquiries": 32, "conversion": 0.094, "size": 32000},
        {"country": "India", "inquiries": 38, "conversion": 0.026, "size": 38000},
        {"country": "Qatar", "inquiries": 28, "conversion": 0.107, "size": 28000},
        {"country": "Russia", "inquiries": 25, "conversion": 0.080, "size": 25000},
        {"country": "Brazil", "inquiries": 18, "conversion": 0.022, "size": 18000}
    ],

    # 6. 通用柱状图：各品类询盘
    "bar_categories": [
        {"category": "OCTG 套管", "value": 380},
        {"category": "工业阀门", "value": 295},
        {"category": "钢结构", "value": 180},
        {"category": "法兰", "value": 145},
        {"category": "钢管", "value": 120},
        {"category": "工具/配件", "value": 80}
    ],

    # 7. 通用饼图：行业分布
    "pie_industries": [
        {"category": "石油天然气", "value": 420},
        {"category": "化工", "value": 230},
        {"category": "建筑", "value": 180},
        {"category": "电力", "value": 150},
        {"category": "矿业", "value": 120},
        {"category": "其他", "value": 100}
    ]
}


def generate_all_demos():
    """生成所有图表类型的 demo HTML"""
    data = HLZD_DEMO_DATA
    data['dashboard']['funnel'] = data['funnel']
    data['dashboard']['geo'] = data['geo']

    today = time.strftime('%Y-%m-%d')
    demos = [
        # (chart_type, data_key, title, file_name)
        ('funnel', data['funnel'], f"销售漏斗图 - {data['period']}", "01_funnel"),
        ('dashboard', data['dashboard'], f"询盘分析看板 - {data['period']}", "02_dashboard"),
        ('geo', data['geo'], "客户地理分布（8 国）", "03_geo"),
        ('bar', data['bar_categories'], "各品类询盘量", "04_bar_categories"),
        ('pie', data['pie_industries'], "行业分布（饼图）", "05_pie_industries"),
        ('line', data['funnel'], "销售趋势（折线）", "06_line_trend"),
        ('heatmap', data['product_region_heatmap'], "产品×地区 热力图（新增）", "07_heatmap"),
    ]

    print("=" * 60)
    print(f"HLZD-D3 综合 Demo 生成器 - {data['company']}")
    print(f"期间: {data['period']}")
    print("=" * 60)

    for chart_type, chart_data, title, name in demos:
        print(f"\n[生成] {name}: {title}")
        try:
            html = build_html(chart_type, chart_data, {
                'title': title,
                'language': 'zh_CN'
            })

            # 手动添加 scatter 散点图（line 用 funnel 数据）
            if chart_type == 'scatter':
                # Line 类型用 funnel stages 数据
                scatter_data = [{'date': f"Day {i+1}", 'value': s['value']} for i, s in enumerate(data['funnel']['stages'])]
                html = build_html('line', scatter_data, {
                    'title': title,
                    'language': 'zh_CN'
                })

            # 保存
            target_path = SKILL_ROOT / 'outputs' / 'dashboards' / today / f"{name}.html"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(html)

            # 写历史
            save_history_entry({
                'chart_type': chart_type,
                'data_source': 'demo',
                'language': 'zh_CN',
                'cost': 0.0,
                'params': {'title': title, 'demo': True}
            }, str(target_path))

            print(f"  ✅ {target_path} ({len(html)} bytes)")
        except Exception as e:
            print(f"  ❌ {e}")

    print("\n" + "=" * 60)
    print("✅ Demo 生成完成")
    print(f"📁 输出目录: outputs/dashboards/{today}/")
    print("=" * 60)
    print("\n💡 双击 HTML 文件即可在浏览器查看（自包含 D3.js CDN）")
    print("💡 7 个 demo 展示了 HLZD-D3 全部图表能力")


if __name__ == '__main__':
    generate_all_demos()