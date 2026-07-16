"""
HLZD-D3可视化 - pytest 共享 fixture
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest


# 确保 scripts 目录可导入
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def temp_dir():
    """临时目录 fixture（自动清理）"""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_funnel_data():
    """漏斗图 Demo 数据"""
    return {
        "stages": [
            {"stage": "询盘", "value": 1000, "conversion_rate": 1.0},
            {"stage": "报价", "value": 500, "conversion_rate": 0.5},
            {"stage": "谈判", "value": 200, "conversion_rate": 0.4},
            {"stage": "成交", "value": 80, "conversion_rate": 0.4}
        ],
        "total_inquiries": 1000,
        "total_deals": 80,
        "overall_conversion": 0.08,
        "period": "2026-07"
    }


@pytest.fixture
def sample_dashboard_data():
    """询盘分析看板 Demo 数据"""
    return {
        "funnel": {
            "stages": [
                {"stage": "询盘", "value": 1000, "conversion_rate": 1.0},
                {"stage": "报价", "value": 500, "conversion_rate": 0.5}
            ],
            "total_inquiries": 1000,
            "total_deals": 80,
            "overall_conversion": 0.08,
            "period": "2026-07"
        },
        "kpi": [
            {"label": "总询盘", "value": "1,000", "color": "#1890FF", "trend": 12},
            {"label": "总成交", "value": "80", "color": "#52C41A", "trend": 8}
        ],
        "trend": [{"date": f"07-{i+1:02d}", "value": 30 + i} for i in range(10)],
        "source": [
            {"source": "阿里", "value": 400},
            {"source": "谷歌", "value": 250}
        ],
        "conversion": [
            {"stage": "询盘→报价", "rate": 0.50},
            {"stage": "报价→成交", "rate": 0.16}
        ],
        "geo": {"points": [
            {"country": "UAE", "count": 50, "lat": 24.4, "lng": 54.4}
        ]},
        "period": "2026-07"
    }


@pytest.fixture
def sample_geo_data():
    """客户地理 Demo 数据"""
    return {
        "points": [
            {"country": "UAE", "count": 50, "lat": 24.4539, "lng": 54.3773},
            {"country": "USA", "count": 25, "lat": 38.9072, "lng": -77.0369},
            {"country": "Germany", "count": 20, "lat": 52.5200, "lng": 13.4050}
        ]
    }


@pytest.fixture
def sample_scatter_data():
    """散点图 Demo 数据（询盘量 vs 成交率）"""
    return {
        "points": [
            {"x": 200, "y": 0.15, "label": "UAE", "category": "中东", "size": 80},
            {"x": 150, "y": 0.12, "label": "Saudi", "category": "中东", "size": 60},
            {"x": 100, "y": 0.18, "label": "Qatar", "category": "中东", "size": 40},
            {"x": 180, "y": 0.10, "label": "USA", "category": "北美", "size": 70},
            {"x": 90,  "y": 0.20, "label": "Germany", "category": "欧洲", "size": 55}
        ],
        "xField": "x",
        "yField": "y",
        "xLabel": "询盘量",
        "yLabel": "成交率"
    }


@pytest.fixture
def sample_chord_data():
    """弦图 Demo 数据（客户-产品关系）"""
    return {
        "links": [
            {"source": "UAE客户", "target": "石油套管", "value": 120},
            {"source": "UAE客户", "target": "阀门", "value": 80},
            {"source": "Saudi客户", "target": "石油套管", "value": 95},
            {"source": "USA客户", "target": "机械设备", "value": 70},
            {"source": "德国客户", "target": "机械设备", "value": 90}
        ]
    }


@pytest.fixture
def sample_force_data():
    """力导向网络 Demo 数据"""
    return {
        "nodes": [
            {"id": "UAE-A", "group": "客户", "size": 30},
            {"id": "USA-A", "group": "客户", "size": 35},
            {"id": "深圳供应商", "group": "供应商", "size": 50},
            {"id": "石油套管", "group": "产品", "size": 60}
        ],
        "links": [
            {"source": "深圳供应商", "target": "石油套管", "value": 5},
            {"source": "UAE-A", "target": "石油套管", "value": 2},
            {"source": "USA-A", "target": "石油套管", "value": 3}
        ]
    }


@pytest.fixture
def sample_csv_funnel(temp_dir):
    """漏斗图 CSV 临时文件"""
    csv_path = temp_dir / 'funnel.csv'
    csv_path.write_text(
        "stage,value,rate\n"
        "询盘,1000,1.0\n"
        "报价,500,0.5\n"
        "谈判,200,0.4\n"
        "成交,80,0.4\n",
        encoding='utf-8'
    )
    return csv_path


@pytest.fixture
def sample_csv_geo(temp_dir):
    """地理 CSV 临时文件"""
    csv_path = temp_dir / 'geo.csv'
    csv_path.write_text(
        "country,count,lat,lng\n"
        "UAE,50,24.4,54.4\n"
        "USA,25,38.9,-77.0\n",
        encoding='utf-8'
    )
    return csv_path


@pytest.fixture
def sample_json_funnel(temp_dir):
    """用户 JSON 数据"""
    json_path = temp_dir / 'my_funnel.json'
    data = {
        "stages": [
            {"stage": "Inquiry", "value": 800, "conversion_rate": 1.0},
            {"stage": "Quote", "value": 400, "conversion_rate": 0.5},
            {"stage": "Won", "value": 60, "conversion_rate": 0.15}
        ],
        "total_inquiries": 800,
        "total_deals": 60,
        "overall_conversion": 0.075
    }
    json_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return json_path


@pytest.fixture
def sample_b2b_report(temp_dir):
    """B2B 报告（markdown 模拟）"""
    md_path = temp_dir / '石油套管B2B市场调研报告.md'
    md_path.write_text(
        "# 石油套管 B2B市场调研报告\n\n"
        "## 一、HS编码确认\n"
        "HS编码：730429\n\n"
        "## 二、市场规模（UN Comtrade 2023）\n"
        "**阿联酋**（UAE）进口：$5,200万\n"
        "**沙特**（Saudi Arabia）进口：$4,800万\n"
        "**美国**（USA）进口：$3,100万\n\n"
        "## 三、买家画像\n"
        "- 矿业/油田营地\n"
        "- EPC/总包\n"
        "## 七、综合建议\n"
        "建议优先开拓中东市场。\n",
        encoding='utf-8'
    )
    return md_path
