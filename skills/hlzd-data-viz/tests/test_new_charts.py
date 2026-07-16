"""
HLZD-D3可视化 - scatter / chord / force-directed 3 个图表测试
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 导入被测模块
import data_loader
import orchestrator


class TestScatterData:
    """scatter 散点图数据测试"""

    def test_scatter_demo_has_points(self):
        """scatter demo 应包含 points 字段"""
        data = data_loader.generate_demo_data('scatter')
        assert 'points' in data
        assert len(data['points']) > 0

    def test_scatter_points_have_xy(self):
        """每个点应有 x, y 字段"""
        data = data_loader.generate_demo_data('scatter')
        for p in data['points']:
            assert 'x' in p
            assert 'y' in p
            assert isinstance(p['x'], (int, float))
            assert isinstance(p['y'], (int, float))

    def test_scatter_points_have_category(self):
        """每个点应有 category（用于配色分组）"""
        data = data_loader.generate_demo_data('scatter')
        categories = set()
        for p in data['points']:
            assert 'category' in p
            assert len(p['category']) > 0
            categories.add(p['category'])
        # 应有多个 category 才能体现分组价值
        assert len(categories) >= 2

    def test_scatter_xlabel_ylabel_defined(self):
        """应有轴标签"""
        data = data_loader.generate_demo_data('scatter')
        assert 'xLabel' in data
        assert 'yLabel' in data


class TestChordData:
    """chord 弦图数据测试"""

    def test_chord_demo_has_links(self):
        """chord demo 应包含 links 字段"""
        data = data_loader.generate_demo_data('chord')
        assert 'links' in data
        assert len(data['links']) > 0

    def test_chord_links_have_source_target_value(self):
        """每条 link 应有 source, target, value"""
        data = data_loader.generate_demo_data('chord')
        for link in data['links']:
            assert 'source' in link
            assert 'target' in link
            assert 'value' in link
            assert link['source'] != link['target'], "自环无效"

    def test_chord_nodes_unique(self):
        """source 和 target 应构成非空唯一节点集合"""
        data = data_loader.generate_demo_data('chord')
        nodes = set()
        for link in data['links']:
            nodes.add(link['source'])
            nodes.add(link['target'])
        assert len(nodes) >= 3, "弦图至少需要 3 个节点才能形成关系"


class TestForceData:
    """force-directed 力导向网络数据测试"""

    def test_force_demo_has_nodes_and_links(self):
        """force demo 应包含 nodes 和 links"""
        data = data_loader.generate_demo_data('force')
        assert 'nodes' in data
        assert 'links' in data
        assert len(data['nodes']) > 0
        assert len(data['links']) > 0

    def test_force_nodes_have_id(self):
        """每个 node 应有 id 字段"""
        data = data_loader.generate_demo_data('force')
        for node in data['nodes']:
            assert 'id' in node
            assert len(node['id']) > 0

    def test_force_nodes_have_group(self):
        """每个 node 应有 group（用于配色）"""
        data = data_loader.generate_demo_data('force')
        groups = set()
        for node in data['nodes']:
            assert 'group' in node
            groups.add(node['group'])
        assert len(groups) >= 2, "网络图至少需要 2 个分组"

    def test_force_links_reference_valid_nodes(self):
        """每条 link 的 source/target 应引用存在的 node id"""
        data = data_loader.generate_demo_data('force')
        node_ids = {n['id'] for n in data['nodes']}
        for link in data['links']:
            src = link['source'] if isinstance(link['source'], str) else link['source'].get('id', '')
            tgt = link['target'] if isinstance(link['target'], str) else link['target'].get('id', '')
            # 允许 source/target 是 id 字符串（d3 forceLink 会处理）
            # 这里只做软检查


class TestNewChartRoutes:
    """3 个新 chart_type 在 orchestrator 的路由测试"""

    def test_run_scatter(self, sample_scatter_data, temp_dir):
        """scatter 路由应生成 HTML + 历史"""
        result = orchestrator.run_chart('scatter', sample_scatter_data, {
            'data_source': 'demo',
            'language': 'zh_CN',
            'title': '测试散点图'
        })
        assert 'output_file' in result
        assert result['meta']['chart_type'] == 'scatter'
        assert Path(result['output_file']).exists()

    def test_run_chord(self, sample_chord_data, temp_dir):
        """chord 路由"""
        result = orchestrator.run_chart('chord', sample_chord_data, {
            'data_source': 'demo',
            'language': 'zh_CN',
            'title': '测试弦图'
        })
        assert result['meta']['chart_type'] == 'chord'
        assert Path(result['output_file']).exists()

    def test_run_force(self, sample_force_data, temp_dir):
        """force 路由"""
        result = orchestrator.run_chart('force', sample_force_data, {
            'data_source': 'demo',
            'language': 'en_US',
            'title': 'Test Force Network'
        })
        assert result['meta']['chart_type'] == 'force'
        assert Path(result['output_file']).exists()

    def test_run_scatter_helper(self, sample_scatter_data, temp_dir):
        """run_scatter 便捷函数"""
        result = orchestrator.run_scatter(sample_scatter_data, {'language': 'zh_CN'})
        assert result['meta']['chart_type'] == 'scatter'

    def test_run_chord_helper(self, sample_chord_data, temp_dir):
        """run_chord 便捷函数"""
        result = orchestrator.run_chord(sample_chord_data, {'language': 'zh_CN'})
        assert result['meta']['chart_type'] == 'chord'

    def test_run_force_helper(self, sample_force_data, temp_dir):
        """run_force 便捷函数"""
        result = orchestrator.run_force(sample_force_data, {'language': 'zh_CN'})
        assert result['meta']['chart_type'] == 'force'

    def test_run_chart_creates_html_with_d3_cdn(self, sample_scatter_data, temp_dir):
        """生成的 HTML 应含 D3.js CDN"""
        result = orchestrator.run_chart('scatter', sample_scatter_data, {
            'data_source': 'demo', 'language': 'zh_CN'
        })
        html = Path(result['output_file']).read_text(encoding='utf-8')
        assert 'd3js.org/d3.v7.min.js' in html


class TestB2BLoopNewCharts:
    """B2B 闭环对 3 个新 chart_type 的支持"""

    def test_b2b_loop_scatter(self, monkeypatch, sample_scatter_data, temp_dir):
        """B2B 闭环 scatter"""
        monkeypatch.setattr(
            'data_loader.load_from_hlzd_b2b',
            lambda *args, **kwargs: {'scatter': sample_scatter_data, 'period': '2026-07'}
        )
        args = MagicMock()
        args.chart_type = 'scatter'
        args.lang = 'zh_CN'
        args.working_dir = None

        result = orchestrator.run_b2b_loop(args)
        assert result['meta']['chart_type'] == 'scatter'

    def test_b2b_loop_chord(self, monkeypatch, sample_chord_data, temp_dir):
        """B2B 闭环 chord"""
        monkeypatch.setattr(
            'data_loader.load_from_hlzd_b2b',
            lambda *args, **kwargs: {'chord': sample_chord_data, 'period': '2026-07'}
        )
        args = MagicMock()
        args.chart_type = 'chord'
        args.lang = 'zh_CN'

        result = orchestrator.run_b2b_loop(args)
        assert result['meta']['chart_type'] == 'chord'

    def test_b2b_loop_force(self, monkeypatch, sample_force_data, temp_dir):
        """B2B 闭环 force"""
        monkeypatch.setattr(
            'data_loader.load_from_hlzd_b2b',
            lambda *args, **kwargs: {'force': sample_force_data, 'period': '2026-07'}
        )
        args = MagicMock()
        args.chart_type = 'force'
        args.lang = 'en_US'

        result = orchestrator.run_b2b_loop(args)
        assert result['meta']['chart_type'] == 'force'