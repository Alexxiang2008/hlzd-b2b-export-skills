"""
HLZD-D3可视化 - orchestrator.py 单元测试
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 导入被测模块（同时也导入 data_loader 用于 monkeypatch）
import orchestrator
import data_loader


class TestRunChart:
    """run_chart 路由测试"""

    def test_run_funnel(self, sample_funnel_data, temp_dir):
        """funnel 路由应生成 HTML + 历史"""
        result = orchestrator.run_chart('funnel', sample_funnel_data, {
            'data_source': 'demo',
            'language': 'zh_CN',
            'title': '测试漏斗'
        })

        assert 'output_file' in result
        assert 'meta' in result
        assert result['meta']['chart_type'] == 'funnel'
        assert Path(result['output_file']).exists()

    def test_run_dashboard(self, sample_dashboard_data, temp_dir):
        """dashboard 路由"""
        result = orchestrator.run_chart('dashboard', sample_dashboard_data, {
            'data_source': 'demo',
            'language': 'zh_CN'
        })
        assert result['meta']['chart_type'] == 'dashboard'
        assert Path(result['output_file']).exists()

    def test_run_geo(self, sample_geo_data, temp_dir):
        """geo 路由"""
        result = orchestrator.run_chart('geo', sample_geo_data, {
            'data_source': 'demo',
            'language': 'en_US'
        })
        assert result['meta']['chart_type'] == 'geo'

    def test_run_chart_creates_html_with_d3_cdn(self, sample_funnel_data, temp_dir):
        """生成的 HTML 应含 D3.js CDN"""
        result = orchestrator.run_chart('funnel', sample_funnel_data, {
            'data_source': 'demo', 'language': 'zh_CN'
        })
        html = Path(result['output_file']).read_text(encoding='utf-8')
        assert 'd3js.org/d3.v7.min.js' in html

    def test_run_chart_saves_to_outputs_dashboards(self, sample_funnel_data, temp_dir):
        """应保存到 outputs/dashboards/{date}/"""
        result = orchestrator.run_chart('funnel', sample_funnel_data, {
            'data_source': 'demo', 'language': 'zh_CN'
        })
        assert 'outputs' in result['output_file']
        assert 'dashboards' in result['output_file']


class TestRunB2BLoop:
    """B2B 闭环测试"""

    def test_b2b_loop_funnel(self, monkeypatch, sample_funnel_data, temp_dir):
        """B2B 闭环 funnel"""
        # Patch data_loader 模块（orchestrator 内部从 data_loader 导入）
        monkeypatch.setattr(
            'data_loader.load_from_hlzd_b2b',
            lambda *args, **kwargs: {'funnel': sample_funnel_data, 'period': '2026-07'}
        )

        args = MagicMock()
        args.chart_type = 'funnel'
        args.lang = 'zh_CN'
        args.working_dir = None

        result = orchestrator.run_b2b_loop(args)
        assert result['meta']['chart_type'] == 'funnel'

    def test_b2b_loop_dashboard(self, monkeypatch, sample_dashboard_data, temp_dir):
        """B2B 闭环 dashboard"""
        monkeypatch.setattr(
            'data_loader.load_from_hlzd_b2b',
            lambda *args, **kwargs: sample_dashboard_data
        )

        args = MagicMock()
        args.chart_type = 'dashboard'
        args.lang = 'en_US'

        result = orchestrator.run_b2b_loop(args)
        assert result['meta']['chart_type'] == 'dashboard'

    def test_b2b_loop_geo(self, monkeypatch, sample_geo_data, temp_dir):
        """B2B 闭环 geo"""
        b2b_data = {'funnel': {}, 'geo': sample_geo_data, 'period': '2026-07'}
        monkeypatch.setattr(
            'data_loader.load_from_hlzd_b2b',
            lambda *args, **kwargs: b2b_data
        )

        args = MagicMock()
        args.chart_type = 'geo'
        args.lang = 'zh_CN'

        result = orchestrator.run_b2b_loop(args)
        assert result['meta']['chart_type'] == 'geo'

    def test_b2b_loop_unsupported_chart_type_raises(self, monkeypatch, sample_funnel_data, temp_dir):
        """不支持的 chart_type 应抛 ValueError"""
        monkeypatch.setattr(
            'data_loader.load_from_hlzd_b2b',
            lambda *args, **kwargs: {'funnel': sample_funnel_data}
        )

        args = MagicMock()
        args.chart_type = 'bar'  # 不在 B2B 循环支持列表
        args.lang = 'zh_CN'

        with pytest.raises(ValueError, match="不支持的 chart_type"):
            orchestrator.run_b2b_loop(args)


class TestMain:
    """main() CLI 入口测试"""

    def test_auto_b2b_requires_chart_type(self, temp_dir, capsys):
        """--auto-b2b 需要 --chart-type"""
        with patch('sys.argv', ['orchestrator.py', '--auto-b2b']):
            with pytest.raises(SystemExit) as exc_info:
                orchestrator.main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert '--auto-b2b 需要 --chart-type' in captured.err

    def test_entities_loads_chart_type(self, sample_funnel_data, temp_dir, monkeypatch):
        """从 entities.json 加载 chart_type"""
        entities_path = temp_dir / 'entities.json'
        entities_path.write_text(json.dumps({
            'chart_type': 'funnel',
            'data_source': 'demo',
            'language': 'zh_CN'
        }), encoding='utf-8')

        with patch('sys.argv', ['orchestrator.py', '--entities', str(entities_path)]):
            with patch.object(orchestrator, 'run_chart') as mock_run:
                mock_run.return_value = {'output_file': '/tmp/test.html', 'meta': {}}
                orchestrator.main()
                mock_run.assert_called_once()
                args = mock_run.call_args
                assert args[0][0] == 'funnel'

    def test_main_routes_to_correct_chart(self, sample_funnel_data, temp_dir, monkeypatch):
        """main() 根据 --chart-type 路由"""
        with patch('sys.argv', ['orchestrator.py', '--chart-type', 'funnel', '--source', 'demo']):
            with patch.object(orchestrator, 'run_chart') as mock_run:
                mock_run.return_value = {'output_file': '/tmp/test.html', 'meta': {}}
                orchestrator.main()
                mock_run.assert_called_once()
                assert mock_run.call_args[0][0] == 'funnel'

    def test_main_user_json_requires_data_file(self):
        """user_json 需 --data-file"""
        with patch('sys.argv', ['orchestrator.py', '--chart-type', 'funnel', '--source', 'user_json']):
            with pytest.raises(SystemExit):
                orchestrator.main()

    def test_main_csv_requires_data_file(self):
        """csv 需 --data-file"""
        with patch('sys.argv', ['orchestrator.py', '--chart-type', 'funnel', '--source', 'csv']):
            with pytest.raises(SystemExit):
                orchestrator.main()

    def test_main_missing_chart_type(self):
        """无 --chart-type 且无 --entities 应报错"""
        with patch('sys.argv', ['orchestrator.py', '--source', 'demo']):
            with pytest.raises(SystemExit) as exc_info:
                orchestrator.main()
            assert exc_info.value.code == 1

    def test_main_hlzd_b2b_with_data_source(self, monkeypatch, temp_dir):
        """--source hlzd_b2b 应调用 run_chart（不直接验证 data 内容）"""
        # 仅验证 run_chart 被调用（不深入 mock data_loader 的内部细节）
        with patch('sys.argv', [
            'orchestrator.py', '--chart-type', 'funnel', '--source', 'hlzd_b2b'
        ]):
            with patch.object(orchestrator, 'run_chart') as mock_run:
                mock_run.return_value = {'output_file': '/tmp/test.html', 'meta': {}}
                orchestrator.main()
                # run_chart 应被调用
                mock_run.assert_called_once()
                # chart_type 是第 1 个位置参数
                assert mock_run.call_args[0][0] == 'funnel'
