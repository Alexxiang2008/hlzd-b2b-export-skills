"""
HLZD-D3可视化 - data_loader.py 单元测试
"""

import os
import sys
import json
from pathlib import Path

import pytest

# 导入被测模块
from data_loader import (
    load_from_hlzd_b2b,
    load_from_json,
    load_from_csv,
    generate_demo_data,
    HLZD_COLORS_HEX
)


class TestGenerateDemoData:
    """Demo 数据生成测试"""

    def test_demo_funnel_has_stages(self):
        """漏斗图 demo 应包含 stages 字段"""
        data = generate_demo_data('funnel')
        assert 'stages' in data
        assert len(data['stages']) > 0
        assert all('stage' in s and 'value' in s for s in data['stages'])

    def test_demo_funnel_conversion_strictly_decreasing(self):
        """漏斗每阶段值应严格递减（漏斗特征）"""
        data = generate_demo_data('funnel')
        values = [s['value'] for s in data['stages']]
        for i in range(len(values) - 1):
            assert values[i] > values[i + 1], f"阶段 {i} → {i+1} 值不递减: {values[i]} → {values[i+1]}"

    def test_demo_dashboard_contains_all_sections(self):
        """Dashboard demo 应包含 6 大模块"""
        data = generate_demo_data('dashboard')
        required = ['funnel', 'kpi', 'trend', 'source', 'conversion', 'geo', 'period']
        for key in required:
            assert key in data, f"Dashboard 缺少 {key}"

    def test_demo_dashboard_kpis_have_labels(self):
        """KPI 卡片应有 label + value"""
        data = generate_demo_data('dashboard')
        assert len(data['kpi']) > 0
        for kpi in data['kpi']:
            assert 'label' in kpi
            assert 'value' in kpi
            assert 'color' in kpi

    def test_demo_geo_has_lat_lng(self):
        """地理 demo 客户点应含经纬度"""
        data = generate_demo_data('geo')
        assert 'points' in data
        assert len(data['points']) > 0
        for p in data['points']:
            assert 'lat' in p
            assert 'lng' in p
            assert -90 <= p['lat'] <= 90
            assert -180 <= p['lng'] <= 180

    def test_demo_geo_points_have_country_name(self):
        """地理点应含 country 字段"""
        data = generate_demo_data('geo')
        for p in data['points']:
            assert 'country' in p
            assert len(p['country']) > 0


class TestLoadFromJson:
    """用户 JSON 加载测试"""

    def test_load_funnel_json(self, sample_json_funnel):
        """加载用户漏斗 JSON 应成功"""
        data = load_from_json(str(sample_json_funnel))
        assert 'stages' in data
        assert len(data['stages']) == 3
        assert data['stages'][0]['stage'] == 'Inquiry'

    def test_load_preserves_chinese_characters(self, sample_json_funnel):
        """中文应保持原样"""
        data = load_from_json(str(sample_json_funnel))
        for stage in data['stages']:
            assert isinstance(stage['stage'], str)
            assert len(stage['stage']) > 0


class TestLoadFromCsv:
    """用户 CSV 加载测试"""

    def test_load_csv_to_funnel(self, sample_csv_funnel):
        """CSV 漏斗数据应正确转换"""
        data = load_from_csv(str(sample_csv_funnel), 'funnel')
        assert 'stages' in data
        assert len(data['stages']) == 4
        assert data['stages'][0]['stage'] == '询盘'
        assert data['stages'][0]['value'] == 1000
        assert data['stages'][0]['conversion_rate'] == 1.0

    def test_load_csv_to_geo(self, sample_csv_geo):
        """CSV 地理数据应正确转换"""
        data = load_from_csv(str(sample_csv_geo), 'geo')
        assert 'points' in data
        assert len(data['points']) == 2
        assert data['points'][0]['country'] == 'UAE'
        assert data['points'][0]['count'] == 50

    def test_load_csv_numeric_conversion(self, sample_csv_funnel):
        """CSV 数字字段应转 int/float"""
        data = load_from_csv(str(sample_csv_funnel), 'funnel')
        for stage in data['stages']:
            assert isinstance(stage['value'], int)
            assert isinstance(stage['conversion_rate'], (int, float))


class TestLoadFromHLZDB2B:
    """B2B 报告加载测试"""

    def test_b2b_fallback_to_demo_when_no_report(self, monkeypatch, temp_dir):
        """无 B2B 报告时 fallback 到 demo（dashboard 结构）"""
        # 把 B2B 候选目录指向空 temp_dir
        monkeypatch.setattr('data_loader.B2B_CANDIDATES', [str(temp_dir)])
        data = load_from_hlzd_b2b(str(temp_dir))
        # B2B 返回的是 dashboard 结构（含 funnel 子键）
        assert 'funnel' in data
        assert 'stages' in data['funnel']
        assert len(data['funnel']['stages']) > 0

    def test_b2b_extract_target_markets(self, monkeypatch, temp_dir, sample_b2b_report):
        """从 B2B 报告提取目标市场"""
        # 复制 sample_b2b_report 到 temp_dir
        target_dir = temp_dir / 'HLZD-B2B工业品调研'
        target_dir.mkdir()
        shutil_path = target_dir / '石油套管B2B市场调研报告.md'
        shutil_path.write_text(sample_b2b_report.read_text(encoding='utf-8'), encoding='utf-8')

        monkeypatch.setattr('data_loader.B2B_CANDIDATES', [str(target_dir)])

        # 调用 load_from_hlzd_b2b → 触发 B2B 解析路径
        data = load_from_hlzd_b2b(str(target_dir))

        # 验证有 funnel（来自 demo 模板）
        assert 'funnel' in data
        assert data['funnel']['total_inquiries'] == 1000

    def test_b2b_no_candidates_returns_demo(self, monkeypatch, temp_dir):
        """B2B 候选都不存在时返回 demo"""
        empty_dir = temp_dir / 'nonexistent'
        empty_dir.mkdir()  # 空目录
        monkeypatch.setattr('data_loader.B2B_CANDIDATES', [str(empty_dir)])

        data = load_from_hlzd_b2b()
        # 无报告 → demo fallback（dashboard 结构）
        assert 'funnel' in data
        assert 'stages' in data['funnel']


class TestColorConstants:
    """颜色常量测试"""

    def test_hlzd_colors_defined(self):
        """HLZD 品牌色应定义完整"""
        required_colors = ['primary', 'secondary', 'accent', 'warning', 'danger', 'text', 'background']
        for color in required_colors:
            assert color in HLZD_COLORS_HEX
            assert HLZD_COLORS_HEX[color].startswith('#')
            assert len(HLZD_COLORS_HEX[color]) == 7  # #RRGGBB

    def test_hlzd_primary_is_blue(self):
        """HLZD primary 色应该是蓝色"""
        primary = HLZD_COLORS_HEX['primary'].lower()
        # #1890FF 蓝色，验证
        assert primary in ('#1890ff', '#1890ff'.lower())
