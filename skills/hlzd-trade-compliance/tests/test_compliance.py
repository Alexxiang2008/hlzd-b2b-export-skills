#!/usr/bin/env python3
"""hlzd-trade-compliance tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402
import check as chk  # noqa: E402
from sources import ofac_sdn, eu_consolidated, bis_entity, country_embargo, dual_use  # noqa: E402
import render_report  # noqa: E402


# ================================================================
# 1. lib helpers
# ================================================================

class TestNormalizeName:
    def test_lowercase_strip(self):
        assert lib.normalize_name("  ACME Co., Ltd.  ") == "acme"

    def test_handles_none(self):
        assert lib.normalize_name(None) == ""

    def test_empty_returns_empty(self):
        assert lib.normalize_name("") == ""


class TestNormalizeCountry:
    def test_alias(self):
        assert lib.normalize_country("UAE") == "united arab emirates"

    def test_china_zh_alias(self):
        assert lib.normalize_country("中国") == "china"

    def test_dprk_alias(self):
        assert lib.normalize_country("DPRK") == "north korea"

    def test_passthrough(self):
        assert lib.normalize_country("Germany") == "germany"


class TestFuzzyIn:
    def test_hit(self):
        assert lib.fuzzy_in("Wagner Group", "wagner")

    def test_miss(self):
        assert not lib.fuzzy_in("Acme Imports", "Wagner")

    def test_empty(self):
        assert not lib.fuzzy_in("", "wagner")
        assert not lib.fuzzy_in("wagner", "")


class TestCountryEmbargoes:
    def test_iran_block(self):
        assert lib.COUNTRY_EMBARGOES["iran"]["severity"] == "BLOCK"

    def test_venezuela_review(self):
        assert lib.COUNTRY_EMBARGOES["venezuela"]["severity"] == "REVIEW"

    def test_kSA_not_in_list(self):
        # Saudi Arabia 在 v0.1 不在 embargo
        assert "saudi arabia" not in lib.COUNTRY_EMBARGOES


class TestDualUseKeywords:
    def test_keywords_present(self):
        for kw in ("dual-use", "encryption", "maraging steel 350"):
            assert kw in lib.DUAL_USE_KEYWORDS


# ================================================================
# 2. Source adapters - data loaded
# ================================================================

@pytest.fixture(scope="module")
def ofac_rows():
    return ofac_sdn._load_rows()


@pytest.fixture(scope="module")
def eu_rows():
    return eu_consolidated._load_rows()


@pytest.fixture(scope="module")
def bis_rows():
    return bis_entity._load_rows()


class TestSdnData:
    def test_load(self, ofac_rows):
        assert len(ofac_rows) >= 20
        names = {r["name"] for r in ofac_rows}
        assert "Hezbollah" in names
        assert "Wagner Group" in names
        assert "Lazarus Group" in names

    def test_hezbollah_match(self, ofac_rows):
        cr = ofac_sdn.check_buyer("Hezbollah Procurement Front", rows=ofac_rows)
        assert cr.matched
        assert any("Hezbollah" in f.evidence for f in cr.flags)

    def test_wagner_match(self, ofac_rows):
        cr = ofac_sdn.check_buyer("Wagner Group Operations LLC", rows=ofac_rows)
        assert cr.matched
        assert any("Wagner" in f.evidence for f in cr.flags)

    def test_acme_no_match(self, ofac_rows):
        cr = ofac_sdn.check_buyer("ACME Industrial Imports", rows=ofac_rows)
        assert not cr.matched
        assert cr.flags == []


class TestEuConsolidatedData:
    def test_load(self, eu_rows):
        assert len(eu_rows) >= 10

    def test_wagner_eu(self, eu_rows):
        cr = eu_consolidated.check_buyer("Wagner Military Group", rows=eu_rows)
        assert cr.matched


class TestBisData:
    def test_huawei_match(self, bis_rows):
        cr = bis_entity.check_buyer("Huawei Technologies Company", rows=bis_rows)
        assert cr.matched
        assert cr.flags[0].severity == "REVIEW"  # BIS is REVIEW, not BLOCK

    def test_karat_match(self, bis_rows):
        cr = bis_entity.check_buyer("Karat Industrial Group Trading", rows=bis_rows)
        assert cr.matched


class TestCountryEmbargoCheck:
    def test_iran_blocked(self):
        cr = country_embargo.check_country("Iran")
        assert cr.matched
        assert cr.flags[0].severity == "BLOCK"

    def test_north_korea_blocked(self):
        cr = country_embargo.check_country("North Korea")
        assert cr.matched
        assert cr.flags[0].severity == "BLOCK"

    def test_venezuela_review(self):
        cr = country_embargo.check_country("Venezuela")
        assert cr.matched
        assert cr.flags[0].severity == "REVIEW"

    def test_saudi_clear(self):
        cr = country_embargo.check_country("Saudi Arabia")
        assert not cr.matched

    def test_end_use_iran(self):
        cr = country_embargo.check_country("UAE", end_use_country="Iran")
        assert cr.matched
        # 来源应该是 end_use_country
        assert cr.flags[0].evidence.startswith("end_use_country")

    def test_both_countries(self):
        cr = country_embargo.check_country("North Korea", end_use_country="Iran")
        assert cr.matched
        # 应该有 2 个 flag（每个 country 一个）
        assert len(cr.flags) == 2


class TestDualUseCheck:
    def test_encryption_keyword(self):
        cr = dual_use.check_product("Encryption module for telecom")
        assert cr.matched
        # 双用途关键词命中
        assert any("encryption" in f.evidence.lower() for f in cr.flags)

    def test_maraging_steel(self):
        cr = dual_use.check_product("Maraging Steel 350 plate")
        assert cr.matched

    def test_hs_code_eccn(self):
        cr = dual_use.check_product("Industrial panel", hs_code="8541.40")
        assert cr.matched
        # HS 8541 命中 ECCN 3A001
        assert any("ECCN-HS-8541" == f.rule_id for f in cr.flags)

    def test_clean_oil_pipe(self):
        cr = dual_use.check_product("Steel API 5CT casing", hs_code="7304.29")
        # 双用途不命中；HS 7304 不在 eccn map
        assert not cr.matched


# ================================================================
# 3. Orchestrator (run_compliance_check)
# ================================================================

class TestOrchestrator:
    def _tx(self, **kw) -> dict:
        base = {
            "buyer_name": "Aramco Trading Co.",
            "buyer_country": "Saudi Arabia",
            "product": "OCTG casing",
            "hs_code": "730429",
            "incoterm": "CIF",
            "value_usd": 850000,
        }
        base.update(kw)
        return base

    def test_clean_cleared(self):
        report = chk.run_compliance_check(self._tx())
        assert report.clearance == "CLEARED"
        assert "Proceed" in report.final_action

    def test_iran_buyer_blocked(self):
        report = chk.run_compliance_check(self._tx(
            buyer_name="Hezbollah Procurement Front",
            buyer_country="Iran",
        ))
        assert report.clearance == "BLOCKED"
        assert "DO NOT ship" in report.final_action
        # 至少应有 4 道检查命中: ofac + eu + bis + country
        block_cr = [cr for cr in report.check_results if cr.matched]
        assert len(block_cr) >= 4

    def test_end_use_iran_only(self):
        # Buyer 是合法的（Saudi），但 end_use 是 Iran → still BLOCKED
        report = chk.run_compliance_check(self._tx(
            buyer_country="Saudi Arabia",
            end_use_country="Iran",
        ))
        assert report.clearance == "BLOCKED"

    def test_review_level_only(self):
        """BIS Entity List only (REVIEW severity) -> PENDING_REVIEW.

        ECCN dual-use keyword alone triggers REVIEW path.
        """
        # buyer 完全干净, product 仅触发 dual-use keyword → REVIEW.
        # 这覆盖 "BIS 未命中的纯 ECCN REVIEW 分支".
        report = chk.run_compliance_check(self._tx(
            buyer_name="Acme Procurement Limited",
            buyer_country="United Kingdom",
            product="encryption module for telecom",
        ))
        # Acme stopwords don't trigger Karat match; dual-use keyword hits ECCN
        assert report.clearance == "PENDING_REVIEW"
        # ECCN REVIEW flag
        eccn_cr = next(cr for cr in report.check_results
                        if "eccn" in cr.check_name)
        assert eccn_cr.matched
        assert all(f.severity == "REVIEW" for f in eccn_cr.flags)

    def test_encryption_keyword_only(self):
        # Buyer clean, product has dual-use keyword → REVIEW
        report = chk.run_compliance_check(self._tx(
            product="encryption module for telecom",
        ))
        assert report.clearance == "PENDING_REVIEW"

    def test_audit_trail_present(self):
        report = chk.run_compliance_check(self._tx())
        assert len(report.audit_trail) == 5  # 5 checks
        for entry in report.audit_trail:
            assert "timestamp_utc" in entry
            assert "check" in entry

    def test_data_versions_recorded(self):
        report = chk.run_compliance_check(self._tx())
        assert len(report.data_versions) == 5
        assert len(report.data_source_attribution) == 5

    def test_to_dict_serializable(self):
        report = chk.run_compliance_check(self._tx())
        d = report.to_dict()
        s = json.dumps(d, ensure_ascii=False)
        restored = json.loads(s)
        assert restored["clearance"] == report.clearance


# ================================================================
# 4. Validation
# ================================================================

class TestInputValidation:
    def test_missing_buyer_name(self):
        with pytest.raises(lib.InvalidInputFormat):
            lib.validate_input({"buyer_country": "US"})

    def test_missing_buyer_country(self):
        with pytest.raises(lib.InvalidInputFormat):
            lib.validate_input({"buyer_name": "Acme"})

    def test_valid_minimal(self):
        lib.validate_input({"buyer_name": "Acme", "buyer_country": "US"})


# ================================================================
# 5. Markdown report renderer
# ================================================================

class TestRenderMarkdown:
    def _minimal_report(self):
        return chk.run_compliance_check({
            "buyer_name": "Aramco Trading Co.",
            "buyer_country": "Saudi Arabia",
            "product": "OCTG casing",
            "hs_code": "730429",
            "incoterm": "CIF",
        }).to_dict()

    def test_renders_cleared(self):
        md = render_report.render_markdown(self._minimal_report())
        assert "[OK]" in md
        assert "CLEARED" in md

    def test_renders_blocked_with_x(self):
        report = chk.run_compliance_check({
            "buyer_name": "Hezbollah Front", "buyer_country": "Iran"
        }).to_dict()
        md = render_report.render_markdown(report)
        assert "[X]" in md
        assert "BLOCKED" in md
        assert "DO NOT ship" in md

    def test_renders_audit_trail(self):
        md = render_report.render_markdown(self._minimal_report())
        assert "Audit Trail" in md

    def test_renders_data_source_attribution(self):
        md = render_report.render_markdown(self._minimal_report())
        assert "Data Source Attribution" in md
        # 5 个 check 都应该有 entry
        assert md.count("static_2026_q3") >= 5

    def test_includes_disclaimer(self):
        md = render_report.render_markdown(self._minimal_report())
        assert "Disclaimer" in md
        assert "v0.1" in md
