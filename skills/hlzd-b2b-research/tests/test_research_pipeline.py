#!/usr/bin/env python3
"""hlzd-b2b-research 测试套件。

覆盖：
1. lib.py: 重试装饰器 / schema 校验 / 文件缓存
2. run_research.py: COUNTRY_HINTS / render_markdown / pipeline 在缺依赖时不崩
3. 子脚本可被 import + 暴露 public API
4. 端到端在不安装外部依赖的情况下，pipeline 输出 warnings 而非崩溃

运行:
    cd skills/hlzd-b2b-research
    py -m pytest tests/ -v --cov=scripts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# 把 scripts/ 加进 path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402
import run_research  # noqa: E402


# ================================================================
# lib.py 测试
# ================================================================

class TestLibErrors:
    def test_research_error_to_dict(self):
        err = lib.ResearchError("oh no", source="test")
        d = err.to_dict()
        assert d["error_class"] == "ResearchError"
        assert d["message"] == "oh no"
        assert d["source"] == "test"

    def test_subclasses_have_source(self):
        for cls in (lib.HSCodeError, lib.TradeDataError, lib.TrendsError, lib.BuyerSearchError):
            err = cls("x")
            assert err.source in ("hs_lookup", "trade_data", "keyword_trends", "buyer_search")


class TestRetry:
    def test_succeeds_first_try(self):
        calls = []

        @lib.retry(max_attempts=3, base_delay=0.01)
        def fn():
            calls.append(1)
            return "ok"

        assert fn() == "ok"
        assert len(calls) == 1

    def test_retries_on_specified_exception(self):
        calls = []

        @lib.retry(max_attempts=3, base_delay=0.01, retry_on=(ValueError,))
        def fn():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "ok"

        assert fn() == "ok"
        assert len(calls) == 3

    def test_raises_after_max_attempts(self):
        calls = []

        @lib.retry(max_attempts=2, base_delay=0.01, retry_on=(ValueError,))
        def fn():
            calls.append(1)
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            fn()
        assert len(calls) == 2


class TestAssertShape:
    def test_missing_keys_raises(self):
        with pytest.raises(lib.ResearchError):
            lib.assert_shape({"keyword": "x"}, "hs_lookup_result")  # missing hs_codes, source

    def test_extra_keys_allowed(self):
        lib.assert_shape({"keyword": "x", "hs_codes": [], "source": "abc", "extra": 1},
                          "hs_lookup_result")

    def test_all_kinds_valid(self):
        for kind in ("hs_lookup_result", "trade_data_result", "trends_result", "buyer_result"):
            lib.assert_shape({k: None for k in lib.REQUIRED_KEYS[kind]}, kind)


class TestFileCache:
    def test_round_trip(self, tmp_path):
        with patch.object(lib, "_DEFAULT_CACHE", tmp_path):
            lib.cache_put("test_key", {"a": 1})
            got = lib.cache_get("test_key")
            assert got == {"a": 1}

    def test_missing_returns_none(self, tmp_path):
        with patch.object(lib, "_DEFAULT_CACHE", tmp_path):
            assert lib.cache_get("nonexistent_key_xyz") is None


class TestLogger:
    def test_get_logger_returns_logger(self):
        logger = lib.get_logger("test_xyz")
        assert isinstance(logger, type(lib.get_logger()))
        assert logger.name == "test_xyz"


# ================================================================
# run_research.py 测试
# ================================================================

class TestCountryHints:
    def test_uae_aliases(self):
        for alias in ("uae", "united arab emirates", "UAE", "United Arab Emirates"):
            key = alias.lower()
            hint = run_research.COUNTRY_HINTS.get(key)
            assert hint is not None, f"missing hint for {alias}"
            assert hint["comtrade"] == "784"

    def test_saudi_aliases(self):
        for alias in ("saudi", "saudi arabia", "Saudi"):
            key = alias.lower()
            hint = run_research.COUNTRY_HINTS.get(key)
            assert hint is not None
            assert hint["comtrade"] == "682"

    def test_us_aliases(self):
        for alias in ("us", "usa"):
            key = alias.lower()
            hint = run_research.COUNTRY_HINTS.get(key)
            assert hint["comtrade"] == "842"


class TestSplitCsv:
    def test_space_separated(self):
        assert run_research._split_csv("UAE Saudi US") == ["UAE", "Saudi", "US"]

    def test_comma_separated(self):
        assert run_research._split_csv("UAE,Saudi,US") == ["UAE", "Saudi", "US"]

    def test_mixed_separators(self):
        assert run_research._split_csv("UAE, Saudi  US") == ["UAE", "Saudi", "US"]

    def test_empty_returns_empty(self):
        assert run_research._split_csv("") == []
        assert run_research._split_csv("   ") == []


class TestRenderMarkdown:
    def test_minimal_report(self):
        report = {
            "product": "OCTG",
            "markets": ["US"],
            "hs_code_candidates": [],
            "trade_data": {"US": {"error": "no api"}},
            "trends": {"US": {"skipped": True}},
            "buyers": {"US": {"total_buyers": 0, "total_tenders": 0, "buyers": [], "tenders": [],
                              "error": "no ddgs"}},
            "warnings": ["[trade_data:US] no api"],
            "hs_code_used": None,
        }
        md = run_research.render_markdown(report)
        assert "OCTG" in md
        assert "市场规模" in md
        assert "需求热度" in md
        assert "买家线索" in md
        assert "Warnings" in md

    def test_with_hs_codes(self):
        report = {
            "product": "OCTG",
            "markets": ["US"],
            "hs_code_candidates": [
                {"hs_code": "730429.10", "name": "石油套管", "rebate": "0", "regulation": "4,x"}
            ],
            "trade_data": {"US": {"hs_code": "730429", "reporter": "us",
                                  "data_source": "UN Comtrade",
                                  "total_import_value_usd": 1.2e9,
                                  "countries": [
                                      {"country": "China", "import_value_usd": 5e8, "share_pct": 41.7},
                                      {"country": "Japan", "import_value_usd": 3e8, "share_pct": 25.0},
                                  ]}},
            "trends": {"US": {"skipped": True}},
            "buyers": {"US": {"skipped": True}},
            "warnings": [],
            "hs_code_used": "730429",
        }
        md = run_research.render_markdown(report)
        assert "730429" in md
        assert "$1.2B" in md or "$1200.0M" in md or "1.2" in md
        assert "China" in md


class TestPipelineGracefulDegradation:
    """关键测试：缺依赖时 pipeline 仍能产出非崩溃结果。"""

    def test_pipeline_runs_without_external_deps(self, capsys):
        """模拟：playwright / pytrends / comtrade / ddgs 全 miss。"""
        with patch.object(run_research, "_step_hs_lookup",
                          return_value={"keyword": "X", "source": "hsbianma.com",
                                         "hs_codes": [], "error": "mock-missing"}), \
             patch.object(run_research, "_step_trade_data",
                          return_value={"hs_code": "123456", "reporter": "us",
                                         "countries": [], "total_import_value_usd": 0,
                                         "data_source": "UN Comtrade", "error": "mock-missing"}), \
             patch.object(run_research, "_step_trends",
                          return_value={"keyword": "X", "geo": "US", "interest_over_time": None,
                                         "related_queries": [], "interest_by_region": None,
                                         "error": "mock-missing"}), \
             patch.object(run_research, "_step_buyer_search",
                          return_value={"total_buyers": 0, "total_tenders": 0,
                                         "buyers": [], "tenders": [], "error": "mock-missing"}):
            report = run_research.run_pipeline("Test Product", ["UAE"], hs_candidate="730429")

        assert report["product"] == "Test Product"
        assert len(report["warnings"]) >= 3, f"expected >=3 warnings, got {report['warnings']}"
        assert any("hs_lookup" in w for w in report["warnings"])
        assert any("trade_data" in w for w in report["warnings"])

    def test_pipeline_picks_hs_from_candidates(self):
        """当 --hs-candidate 没传时，pipeline 从 hs_lookup 结果里挑 6 位。"""
        with patch.object(run_research, "_step_hs_lookup",
                          return_value={"keyword": "X", "source": "hsbianma.com",
                                         "hs_codes": [{"hs_code": "730429.10", "name": "Test"}]}), \
             patch.object(run_research, "_step_trade_data",
                          return_value={"countries": [], "total_import_value_usd": 0,
                                         "data_source": "UN Comtrade", "error": "skip"}), \
             patch.object(run_research, "_step_trends",
                          return_value={"keyword": "X", "interest_over_time": None,
                                         "related_queries": [], "interest_by_region": None,
                                         "error": "skip"}), \
             patch.object(run_research, "_step_buyer_search",
                          return_value={"total_buyers": 0, "total_tenders": 0, "buyers": [], "tenders": []}):
            report = run_research.run_pipeline("Test", ["US"])

        assert report["hs_code_used"] == "730429"


# ================================================================
# 子脚本存在性 + 可 import
# ================================================================

class TestSubScriptsImportable:
    """子脚本可能 require 外部依赖（playwright / pytrends / comtrade / ddgs）。

    关键验证：(1) 文件存在 (2) Python 语法 OK。
    不直接 import（避免 module-level 副作用 / capture 问题）。
    """

    def test_lib_importable(self):
        import lib
        assert hasattr(lib, "ResearchError")

    def test_run_research_importable(self):
        import run_research
        assert hasattr(run_research, "run_pipeline")
        assert hasattr(run_research, "render_markdown")

    @pytest.mark.parametrize("name", ["hs_lookup", "trade_data", "keyword_trends", "buyer_search", "lib", "run_research"])
    def test_subscript_file_parses(self, name):
        path = Path(__file__).parent.parent / "scripts" / f"{name}.py"
        assert path.exists(), f"missing {path}"
        # Syntax check via py_compile — catches SyntaxError without executing module body
        import py_compile
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"{name}.py has SyntaxError: {exc}")


class TestRequirements:
    def test_requirements_lists_known_deps(self):
        req_path = Path(__file__).parent.parent / "scripts" / "requirements.txt"
        assert req_path.exists(), "scripts/requirements.txt missing"
        req = req_path.read_text(encoding="utf-8")
        for must in ("comtradeapicall", "pytrends", "ddgs", "playwright", "pandas"):
            assert must in req, f"{must} missing from requirements.txt"
