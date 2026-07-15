#!/usr/bin/env python3
"""hlzd-buyer-finder 测试套件。

覆盖：
1. lib.py: RateLimiter / dedup / classify_volza_response / normalize /
   extract_company_candidates_from_text / stable_id
2. pipeline: 3 链路编排（mock http_get），验证产出 schema + dedup + quota
3. CLI: 参数校验 + 输出 schema

运行：
  cd skills/hlzd-buyer-finder
  py -m pytest tests/ -v --cov=scripts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 让 scripts 可 import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402
import pipeline  # noqa: E402
from cli import cli, _parse_csv  # noqa: E402


# ================================================================
# 1. lib.py — RateLimiter
# ================================================================

class TestRateLimiter:
    def test_first_call_allowed(self, tmp_path):
        state = tmp_path / "state.json"
        lim = lib.RateLimiter("test", min_interval_sec=0,
                               daily_quota=10, state_path=state)
        allowed, why = lim.can_call()
        assert allowed is True
        assert why == "ok"

    def test_daily_quota_enforced(self, tmp_path):
        state = tmp_path / "state.json"
        lim = lib.RateLimiter("test", min_interval_sec=0,
                               daily_quota=2, state_path=state)
        lim.record_call()
        lim.record_call()
        allowed, why = lim.can_call()
        assert allowed is False
        assert "quota" in why

    def test_min_interval_enforced(self, tmp_path):
        state = tmp_path / "state.json"
        lim = lib.RateLimiter("test", min_interval_sec=999,
                               daily_quota=10, state_path=state)
        lim.record_call()
        allowed, why = lim.can_call()
        assert allowed is False
        assert "interval" in why

    def test_reset_clears(self, tmp_path):
        state = tmp_path / "state.json"
        lim = lib.RateLimiter("test", min_interval_sec=0,
                               daily_quota=2, state_path=state)
        lim.record_call(); lim.record_call()
        lim.reset()
        assert lim.can_call()[0] is True

    def test_state_persists(self, tmp_path):
        state = tmp_path / "state.json"
        lim1 = lib.RateLimiter("persist", min_interval_sec=0,
                                daily_quota=5, state_path=state)
        lim1.record_call()
        # 重新加载
        lim2 = lib.RateLimiter("persist", min_interval_sec=0,
                                daily_quota=5, state_path=state)
        # 同一天应记为已用 1 次
        assert lim2._state["count"] == 1

    def test_status(self, tmp_path):
        state = tmp_path / "state.json"
        lim = lib.RateLimiter("test", min_interval_sec=2.5,
                               daily_quota=10, state_path=state)
        s = lim.status()
        assert s["name"] == "test"
        assert s["quota"] == 10
        assert s["min_interval_sec"] == 2.5
        assert s["used"] == 0


# ================================================================
# 2. lib.py — Dedup
# ================================================================

class TestDedup:
    def test_dedup_by_company_name(self):
        recs = [
            {"importer_name": "Acme Co., Ltd.", "value_usd": 1000},
            {"importer_name": "ACME Limited", "value_usd": 5000},
            {"importer_name": "Different LLC", "value_usd": 2000},
        ]
        out = lib.dedup_importers(recs)
        # 第一个 Acme (1000) 与 ACME Limited (5000) 视为同一公司（normalize 都成 acme），
        # 保留 5000。Different LLC 保留
        names = [r["importer_name"] for r in out]
        assert any("ACME" in n for n in names)
        assert any("Different" in n for n in names)
        # 高 value 的保留
        acme = next(r for r in out if "ACME" in r["importer_name"])
        assert acme["value_usd"] == 5000

    def test_dedup_by_url_when_no_name(self):
        recs = [
            {"url": "https://example.com/buyer1", "value_usd": 1000},
            {"url": "https://Example.com/buyer1", "value_usd": 5000},
        ]
        out = lib.dedup_importers(recs)
        assert len(out) == 1
        assert out[0]["value_usd"] == 5000

    def test_dedup_sort_by_value(self):
        recs = [
            {"importer_name": "Low Co.", "value_usd": 10},
            {"importer_name": "High Co.", "value_usd": 1000000},
            {"importer_name": "Mid Co.", "value_usd": 1000},
        ]
        out = lib.dedup_importers(recs)
        assert out[0]["importer_name"] == "High Co."
        assert out[-1]["importer_name"] == "Low Co."

    def test_dedup_handles_empty_input(self):
        assert lib.dedup_importers([]) == []

    def test_dedup_handles_anon_records(self):
        """无 name 无 url 时不崩。"""
        recs = [{"x": 1}, {"x": 2}, {"x": 3}]
        out = lib.dedup_importers(recs)
        assert len(out) == 3


# ================================================================
# 3. lib.py — Volza response classification
# ================================================================

class TestVolzaClassifier:
    def test_blocked_body(self):
        # 11055 ± 50
        body = "x" * 11055
        assert lib.classify_volza_response(body) == "blocked"

    def test_blocked_near_threshold_low(self):
        body = "x" * 11000
        assert lib.classify_volza_response(body) == "blocked"

    def test_blocked_near_threshold_high(self):
        body = "x" * 11100
        assert lib.classify_volza_response(body) == "blocked"

    def test_success_body(self):
        body = "x" * 16500
        assert lib.classify_volza_response(body) == "success"

    def test_loading_body(self):
        body = "x" * 12500
        assert lib.classify_volza_response(body) == "loading"

    def test_unknown_short(self):
        body = "x" * 500
        assert lib.classify_volza_response(body) == "unknown"

    def test_with_explicit_body_len(self):
        assert lib.classify_volza_response("ignored", body_len=11055) == "blocked"
        assert lib.classify_volza_response("ignored", body_len=16500) == "success"


# ================================================================
# 4. lib.py — Company name helpers
# ================================================================

class TestCompanyHelpers:
    def test_normalize_strip_suffix(self):
        assert lib.normalize_company_name("Acme Co., Ltd.") == "acme"
        assert lib.normalize_company_name("Acme Limited") == "acme"
        assert lib.normalize_company_name("Acme LLC") == "acme"
        assert lib.normalize_company_name("Acme Inc.") == "acme"
        assert lib.normalize_company_name("Acme Corp.") == "acme"
        assert lib.normalize_company_name("Acme GmbH") == "acme"
        assert lib.normalize_company_name("Acme S.A.") == "acme"

    def test_normalize_lowercase_strips_spaces(self):
        assert lib.normalize_company_name("  ACME  ") == "acme"

    def test_extract_company_candidates(self):
        text = """
        Xiamen Hym Metal Products Co., Ltd.
        Some random line
        Shenzhen Kaier Wo Prototyping Technology Co., Ltd.
        Another line
        Hubei Xinjie Industrial Group
        China-only line
        Wikipedia article
        """
        out = lib.extract_company_candidates_from_text(text)
        names = " ".join(out)
        assert "Xiamen" in names
        assert "Shenzhen" in names
        assert "Hubei" in names
        # 中文夹杂应被剔除
        assert "China-only" not in names

    def test_extract_filters_length(self):
        text = "AB\n" * 200  # 全短
        out = lib.extract_company_candidates_from_text(text)
        for n in out:
            assert 4 <= len(n) <= 120


# ================================================================
# 5. lib.py — assertion & misc
# ================================================================

class TestAssertShape:
    def test_missing_keys_raises(self):
        with pytest.raises(lib.BuyerFinderError) as exc_info:
            lib.assert_shape({"product": "x"}, "pipeline_report")
        assert "missing" in str(exc_info.value).lower()

    def test_valid_passes(self):
        rec = {
            "product": "x", "country": "US", "method": "auto",
            "competitors": [], "importers": [], "warnings": [],
        }
        lib.assert_shape(rec, "pipeline_report")  # 不应抛

    def test_importer_record(self):
        good = {
            "importer_name": "Acme", "country": "US",
            "url": "https://acme.example",
        }
        lib.assert_shape(good, "importer_record")
        bad = {"importer_name": "Acme"}  # missing country, url
        with pytest.raises(lib.BuyerFinderError):
            lib.assert_shape(bad, "importer_record")


class TestErrorsHierarchy:
    def test_source_blocked_recoverable(self):
        e = lib.SourceBlockedError("blocked", "volza")
        assert e.source == "volza"
        assert e.recoverable is True

    def test_invalid_param_not_recoverable(self):
        e = lib.InvalidParameterError("bad arg")
        assert e.recoverable is False


class TestStableId:
    def test_same_payload_same_id(self):
        a = lib.stable_id({"x": 1})
        b = lib.stable_id({"x": 1})
        assert a == b

    def test_different_payload_different_id(self):
        a = lib.stable_id({"x": 1})
        b = lib.stable_id({"x": 2})
        assert a != b

    def test_prefix_included(self):
        assert lib.stable_id({}, "abc").startswith("abc:")


# ================================================================
# 6. pipeline — auto / competitor / keyword
# ================================================================

def _alibaba_fixture() -> str:
    return """
    Random ad text
    Xiamen Hym Metal Products Co., Ltd.
    Random line
    Shenzhen Kaier Wo Prototyping Technology Co., Ltd.
    Random
    Hubei Xinjie Industrial Group Co., Ltd.
    """


def _volza_fixture_blocked() -> str:
    """body 长度 ≈ 11055，触发 blocked detection。"""
    return "x" * 11055


def _volza_fixture_success(buyers: list) -> str:
    """Build a Volza-like HTML with buyer rows in <table>."""
    rows = ""
    for b in buyers:
        rows += f"<tr><td>{b['importer_name']}</td><td>{b['country']}</td><td>China</td><td>{b['quantity']}</td><td>{b['value']}</td><td>{b['date']}</td></tr>"
    html = f"<html><body><table><tbody>{rows}</tbody></table></body></html>"
    return html


class TestPipelineAuto:
    def test_alibaba_captcha_yields_fallback(self, tmp_path):
        """阿里 captcha → fallback_seed competitor → Volza 也失败 → warnings 完整。"""
        with patch.object(lib, "RateLimiter", autospec=True) as mock_lim, \
             patch("sources.alibaba.search_alibaba_competitors",
                    return_value=([], ["alibaba_captcha_triggered"])), \
             patch("sources.volza.search_volza_for_competitor",
                    return_value=([], ["volza_network_error"])):
            from lib import RateLimiter
            mock_lim.return_value.can_call.return_value = (True, "ok")
            mock_lim.return_value.record_call = MagicMock()
            out = pipeline.run_auto("Test", country_iso="US",
                                     volza_quota_override=(0, 100),
                                     alibaba_quota_override=(0, 100))

        assert out["method"] == "auto"
        assert any("captcha" in w.lower() for w in out["warnings"])
        assert out["competitors"], "fallback seed should populate competitors"

    def test_alibaba_yields_real_competitors_then_volza_extracted(self):
        alibaba_companies = [
            {"company_name": "Xiamen Hym Metal Products Co., Ltd.", "source": "alibaba.com"},
            {"company_name": "Shenzhen Kaier Wo Prototyping Technology Co., Ltd.", "source": "alibaba.com"},
        ]
        buyers = [
            {"importer_name": "ABC Machinery Inc", "country": "United States",
             "quantity": "500 units", "value": "$125,000", "date": "2025-03"},
            {"importer_name": "DEF Industrial Co", "country": "United States",
             "quantity": "200 units", "value": "$50,000", "date": "2025-04"},
            # duplicate of first (case-different)
            {"importer_name": "ABC MACHINERY INC", "country": "United States",
             "quantity": "100 units", "value": "$25,000", "date": "2025-05"},
        ]
        with patch("sources.alibaba.search_alibaba_competitors",
                    return_value=(alibaba_companies, [])), \
             patch("sources.volza.search_volza_for_competitor",
                    side_effect=[
                        (buyers[:2], []),
                        ([buyers[2]], []),
                    ]):
            with patch.object(lib, "RateLimiter",
                              side_effect=lambda *args, **kw:
                              MagicMock(can_call=MagicMock(return_value=(True, "ok")),
                                         record_call=MagicMock())):
                out = pipeline.run_auto("Test", country_iso="US",
                                         volza_quota_override=(0, 100),
                                         alibaba_quota_override=(0, 100))

        assert out["method"] == "auto"
        assert out["stats"]["competitors_found"] == 2
        assert out["stats"]["volza_quota_used"] == 2
        # 3 个原始 buyers，dedup 后 2 unique（ABC + DEF）
        assert out["stats"]["importers_found_pre_dedup"] == 3
        assert out["stats"]["importers_after_dedup"] == 2
        # 保留高 value 的
        names = [r["importer_name"] for r in out["importers"]]
        assert "ABC Machinery Inc" in names
        assert "DEF Industrial Co" in names


class TestPipelineCompetitor:
    def test_competitor_method_passes_names_through(self):
        buyers = [
            {"importer_name": "Acme Inc", "country": "US", "quantity": "10",
             "value": "$1000", "date": "2025-01"},
        ]
        with patch("sources.volza.search_volza_for_competitor",
                    return_value=(buyers, [])), \
             patch.object(lib, "RateLimiter",
                          side_effect=lambda *a, **kw:
                          MagicMock(can_call=MagicMock(return_value=(True, "ok")),
                                     record_call=MagicMock())):
            out = pipeline.run_competitor_list(["ACME Industrial Co."],
                                                country_iso="US",
                                                volza_quota_override=(0, 100))
        assert out["method"] == "competitor"
        assert out["competitors"] == [{"company_name": "ACME Industrial Co.",
                                          "source": "user_provided"}]
        assert len(out["importers"]) == 1

    def test_competitor_requires_list(self):
        with pytest.raises(lib.InvalidParameterError):
            pipeline.run_pipeline("foo", method="competitor", competitors=None)


class TestPipelineKeyword:
    def test_keyword_method_combines_sources(self):
        keyword_buyers = [
            {"importer_name": "Mfg Co", "country": "US", "value": "$100"},
        ]
        volza_buyers = [
            {"importer_name": "Import LLC", "country": "US", "value": "$500"},
        ]
        with patch("sources.volza.search_volza_by_country",
                    return_value=(volza_buyers, [])), \
             patch("sources.keyword.search_keyword_public",
                    return_value=(keyword_buyers, [])):
            out = pipeline.run_keyword("Test Prod", "US")
        assert out["method"] == "keyword"
        # 2 unique
        assert len(out["importers"]) == 2


class TestPipelineDispatch:
    def test_unknown_method_raises(self):
        with pytest.raises(lib.InvalidParameterError):
            pipeline.run_pipeline("x", method="bogus_method")

    def test_keyword_requires_country(self):
        with pytest.raises(lib.InvalidParameterError):
            pipeline.run_pipeline("x", method="keyword", country_iso=None)

    def test_auto_default(self):
        with patch("sources.alibaba.search_alibaba_competitors",
                    return_value=([], ["alibaba_blocked"])), \
             patch("sources.volza.search_volza_for_competitor",
                    return_value=([], [])), \
             patch.object(lib, "RateLimiter",
                          side_effect=lambda *a, **kw:
                          MagicMock(can_call=MagicMock(return_value=(True, "ok")),
                                     record_call=MagicMock())):
            out = pipeline.run_pipeline("prod", country_iso="US",
                                          volza_quota_override=(0, 100),
                                          alibaba_quota_override=(0, 100))
        assert out["method"] == "auto"


# ================================================================
# 7. CLI 参数解析
# ================================================================

class TestParseCsv:
    def test_comma_separated(self):
        assert _parse_csv("a,b,c") == ["a", "b", "c"]

    def test_newline_separated(self):
        assert _parse_csv("a\nb\nc") == ["a", "b", "c"]

    def test_empty(self):
        assert _parse_csv("") == []
        assert _parse_csv("   ") == []


class TestCLIPath:
    def test_competitor_method_requires_competitor_arg(self, capsys):
        with patch("sys.argv", ["cli", "--method", "competitor"]):
            rc = cli()
        assert rc == 2
        captured = capsys.readouterr()
        assert "--competitor" in captured.err

    def test_keyword_method_requires_country(self, capsys):
        with patch("sys.argv", ["cli", "--product", "x", "--method", "keyword"]):
            rc = cli()
        assert rc == 2

    def test_auto_method_with_country(self):
        with patch("pipeline.run_pipeline",
                    return_value={"importers": [{"importer_name": "A"}],
                                    "warnings": [], "stats": {}}), \
             patch("sys.argv", ["cli", "--product", "CNC", "--country", "US"]):
            rc = cli()
        assert rc == 0


# ================================================================
# 8. Pipeline output schema 完整性
# ================================================================

class TestOutputSchema:
    def test_auto_output_has_required_keys(self):
        with patch("sources.alibaba.search_alibaba_competitors",
                    return_value=([], [])), \
             patch("sources.volza.search_volza_for_competitor",
                    return_value=([], [])), \
             patch.object(lib, "RateLimiter",
                          side_effect=lambda *a, **kw:
                          MagicMock(can_call=MagicMock(return_value=(True, "ok")),
                                     record_call=MagicMock())):
            out = pipeline.run_pipeline("Test", country_iso="US",
                                          volza_quota_override=(0, 100),
                                          alibaba_quota_override=(0, 100))

        # 必含 key
        for k in ("product", "country", "method", "competitors", "importers", "warnings", "stats"):
            assert k in out, f"missing {k}"

        # stats 子集
        for k in ("competitors_found", "importers_found_pre_dedup",
                   "importers_after_dedup", "volza_quota_used", "alibaba_quota_used"):
            assert k in out["stats"], f"missing stats.{k}"
