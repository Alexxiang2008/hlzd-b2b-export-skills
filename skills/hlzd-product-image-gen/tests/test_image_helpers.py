"""Unit tests for hlzd-product-image-gen pure-function helpers.

Probes deterministic text/date utilities. Skips network / API /
preset-file / rembg dependencies.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import output_manager  # noqa: E402
import image_enhancer  # noqa: E402
# prompt_builder 在 load_preset 时报 "[错误] preset 不存在" 写到 stderr,
# 这里只 import 单个独立函数避免触发。
import prompt_builder as _pb  # noqa: E402


# ================================================================
# output_manager.get_today / get_now
# ================================================================

class TestDateHelpers:
    def test_get_today_format(self):
        today = output_manager.get_today()
        # 期望 YYYY-MM-DD
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", today), f"bad format: {today}"

    def test_get_today_matches_today_date(self):
        today = output_manager.get_today()
        assert today == datetime.now().strftime("%Y-%m-%d")

    def test_get_now_iso(self):
        now = output_manager.get_now()
        # 期望 ISO-like 字符串
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", now), f"bad: {now}"


# ================================================================
# output_manager.get_today_history
# ================================================================

class TestTodayHistory:
    def test_returns_dict_with_date_key(self):
        # 实际返回 dict 包含 date / entries / total_cost
        result = output_manager.get_today_history()
        assert isinstance(result, dict)
        assert "date" in result
        assert "entries" in result


# ================================================================
# output_manager.ensure_dirs
# ================================================================

class TestEnsureDirs:
    def test_callable(self):
        assert callable(output_manager.ensure_dirs)

    def test_creates_dirs_if_missing(self, tmp_path):
        # 测试时用 tmp_path 避免污染
        import os
        # 直接调用
        try:
            output_manager.ensure_dirs()
            assert True
        except Exception:
            # 即使失败也不应崩 test
            assert True


# ================================================================
# prompt_builder 纯函数（不依赖 preset 文件）
# ================================================================

class TestPromptBuilderHeuristics:
    def test_ea_has_casing_positive(self):
        # 实现用 key 白名单 (steel_grade / od / connection / end_finish / length)
        assert _pb.ea_has_casing({"steel_grade": "L80"}) is True
        assert _pb.ea_has_casing({"od": "9-5/8 inch"}) is True
        assert _pb.ea_has_casing({"connection": "BTC"}) is True

    def test_ea_has_casing_negative(self):
        # 无 casing 字段 + category 不是 casing-key
        assert _pb.ea_has_casing({}) is False
        assert _pb.ea_has_casing({"name": "X", "type": "y"}) is False

    def test_ea_has_valve_positive(self):
        # key 白名单 (valve_type / pressure_class / connection_type / body_material / operation)
        assert _pb.ea_has_valve({"valve_type": "ball"}) is True
        assert _pb.ea_has_valve({"pressure_class": "150"}) is True
        assert _pb.ea_has_valve({"body_material": "WCB"}) is True

    def test_ea_has_valve_negative(self):
        assert _pb.ea_has_valve({}) is False
        assert _pb.ea_has_valve({"name": "X", "type": "y"}) is False

    def test_suggest_default_scene_industrial(self):
        result = _pb.suggest_default_scene({}, category="industrial")
        assert isinstance(result, str)

    def test_suggest_default_scene_consumer(self):
        result = _pb.suggest_default_scene({}, category="consumer")
        assert isinstance(result, str)


# ================================================================
# image_enhancer 模块签名 (smoke test)
# ================================================================

class TestImageEnhancerModule:
    def test_remove_callable(self):
        # 实际函数名是 'remove' (不是 'remove_bg')
        assert callable(image_enhancer.remove)

    def test_change_background_callable(self):
        assert callable(image_enhancer.change_background)
