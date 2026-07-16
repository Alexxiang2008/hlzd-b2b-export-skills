"""
HLZD-D3可视化 - output_manager.py 单元测试
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# 导入被测模块
import output_manager
from output_manager import (
    ensure_dirs,
    get_today,
    get_now,
    get_today_history,
    save_history_entry,
    save_html
)


class TestEnsureDirs:
    """ensure_dirs 测试"""

    def test_ensure_dirs_creates_directories(self, temp_dir, monkeypatch):
        """应创建 outputs/dashboards 和 outputs/history"""
        # 重定向 OUTPUTS_DIR 到 temp_dir
        monkeypatch.setattr(output_manager, 'OUTPUTS_DIR', temp_dir / 'outputs')
        monkeypatch.setattr(output_manager, 'DASHBOARDS_DIR', temp_dir / 'outputs' / 'dashboards')
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'outputs' / 'history')

        ensure_dirs()

        assert (temp_dir / 'outputs' / 'dashboards').exists()
        assert (temp_dir / 'outputs' / 'history').exists()


class TestHistoryEntry:
    """历史 entry 测试"""

    def test_save_history_entry_creates_entry(self, monkeypatch, temp_dir):
        """保存历史 entry 应成功"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        meta = {
            'chart_type': 'funnel',
            'data_source': 'demo',
            'language': 'zh_CN'
        }
        entry = save_history_entry(meta, '/tmp/test.html')

        assert entry['chart_type'] == 'funnel'
        assert entry['language'] == 'zh_CN'
        assert 'timestamp' in entry
        assert entry['output_file'] == '/tmp/test.html'

    def test_save_history_increments_count(self, monkeypatch, temp_dir):
        """多次保存应累加 count"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        for i in range(3):
            save_history_entry({'chart_type': 'funnel'}, f'/tmp/test_{i}.html')

        history = get_today_history()
        assert history['total_count'] == 3
        assert len(history['entries']) == 3

    def test_save_history_cost_field(self, monkeypatch, temp_dir):
        """cost 字段应为 0.0（无 API 调用）"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        entry = save_history_entry({'chart_type': 'bar'}, '/tmp/test.html')
        assert entry['cost'] == 0.0

    def test_save_history_with_io_error_raises(self, monkeypatch, temp_dir):
        """IOError 时应抛 IOError"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        # Mock open 失败
        original_open = open
        def failing_open(*args, **kwargs):
            if 'history' in str(args[0]):
                raise IOError("磁盘满")
            return original_open(*args, **kwargs)

        with patch('builtins.open', side_effect=failing_open):
            with pytest.raises(IOError, match="历史 JSON 写入失败"):
                save_history_entry({'chart_type': 'bar'}, '/tmp/test.html')


class TestGetTodayHistory:
    """get_today_history 测试"""

    def test_get_today_history_empty_initially(self, monkeypatch, temp_dir):
        """首次调用应返回空结构"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        history = get_today_history()
        assert 'date' in history
        assert 'entries' in history
        assert 'total_count' in history
        assert history['total_count'] == 0

    def test_get_today_history_corrupt_json_returns_empty(self, monkeypatch, temp_dir):
        """损坏的 JSON 应返回空结构（不抛错）"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        # 写入损坏 JSON
        corrupt_path = temp_dir / 'history' / f'{get_today()}.json'
        corrupt_path.write_text('{ invalid json', encoding='utf-8')

        history = get_today_history()
        # 应回退到空结构
        assert history['total_count'] == 0


class TestSaveHtml:
    """save_html 测试"""

    def test_save_html_creates_file(self, monkeypatch, temp_dir):
        """应创建 HTML 文件"""
        monkeypatch.setattr(output_manager, 'DASHBOARDS_DIR', temp_dir / 'dashboards')
        output_manager.ensure_dirs()

        html_content = '<html><body>Test</body></html>'
        path = save_html(html_content, 'test.html')

        assert Path(path).exists()
        content = Path(path).read_text(encoding='utf-8')
        assert content == html_content

    def test_save_html_uses_suggested_name(self, monkeypatch, temp_dir):
        """应使用建议的文件名"""
        monkeypatch.setattr(output_manager, 'DASHBOARDS_DIR', temp_dir / 'dashboards')
        output_manager.ensure_dirs()

        path = save_html('<html></html>', 'my_chart_20260706.html')
        assert path.endswith('my_chart_20260706.html')

    def test_save_html_creates_today_subdir(self, monkeypatch, temp_dir):
        """应按日期分目录"""
        monkeypatch.setattr(output_manager, 'DASHBOARDS_DIR', temp_dir / 'dashboards')
        output_manager.ensure_dirs()

        path = save_html('<html></html>', 'test.html')
        today = get_today()
        assert today in path


class TestMain:
    """main() CLI 入口测试"""

    def test_main_save_subcommand(self, monkeypatch, temp_dir):
        """save 子命令应保存 HTML + 写历史"""
        # 重定向目录
        monkeypatch.setattr(output_manager, 'DASHBOARDS_DIR', temp_dir / 'dashboards')
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')

        # 创建临时 HTML
        html_path = temp_dir / 'input.html'
        html_path.write_text('<html></html>', encoding='utf-8')

        meta_path = temp_dir / 'meta.json'
        meta_path.write_text(json.dumps({
            'chart_type': 'funnel',
            'data_source': 'demo',
            'language': 'zh_CN'
        }), encoding='utf-8')

        with patch('sys.argv', [
            'output_manager.py', 'save',
            '--meta', str(meta_path),
            '--html', str(html_path),
            '--name', 'output.html'
        ]):
            output_manager.main()

        # 验证文件已保存
        assert (temp_dir / 'dashboards' / get_today() / 'output.html').exists()
        # 验证历史已写
        assert (temp_dir / 'history' / f'{get_today()}.json').exists()

    def test_main_history_subcommand(self, monkeypatch, temp_dir, capsys):
        """history 子命令应输出历史"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        # 写一条历史
        save_history_entry({'chart_type': 'funnel'}, '/tmp/test.html')

        with patch('sys.argv', ['output_manager.py', 'history', '--today']):
            output_manager.main()

        captured = capsys.readouterr()
        assert 'funnel' in captured.out

    def test_main_history_specific_date(self, monkeypatch, temp_dir, capsys):
        """--date 参数应读取指定日期"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        # 写一条历史
        save_history_entry({'chart_type': 'geo'}, '/tmp/test.html')

        with patch('sys.argv', [
            'output_manager.py', 'history', '--date', get_today()
        ]):
            output_manager.main()

        captured = capsys.readouterr()
        assert 'geo' in captured.out

    def test_main_history_missing_date(self, monkeypatch, temp_dir):
        """--date 无数据时输出警告（不抛错）"""
        monkeypatch.setattr(output_manager, 'HISTORY_DIR', temp_dir / 'history')
        output_manager.ensure_dirs()

        # 直接调用不应抛错
        with patch('sys.argv', [
            'output_manager.py', 'history', '--date', '2020-01-01'
        ]):
            # 仅验证不抛错（输出在 Windows GBK 环境下可能丢失）
            try:
                output_manager.main()
            except SystemExit:
                pass  # OK, 退出 0

    def test_main_requires_subcommand(self, capsys):
        """必须指定子命令"""
        with patch('sys.argv', ['output_manager.py']):
            with pytest.raises(SystemExit):
                output_manager.main()
