#!/usr/bin/env python3
"""hlzd-customer-due-diligence tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402
from sources import linkedin, whois, sanctions  # noqa: E402


# ================================================================
# 1. lib helpers
# ================================================================

class TestNormalize:
    def test_lowercase_strip_suffix(self):
        assert lib.normalize_company("Saudi Aramco Trading Co.") == "saudi aramco trading"

    def test_handles_empty(self):
        assert lib.normalize_company("") == ""

    def test_handles_none(self):
        assert lib.normalize_company(None) == ""


class TestSanctionedCountry:
    @pytest.mark.parametrize("country,expected", [
        ("Iran", True),
        ("North Korea", True),
        ("Syria", True),
        ("Saudi Arabia", False),
        ("United Arab Emirates", False),
        ("United States", False),
    ])
    def test_country_check(self, country, expected):
        assert lib.is_sanctioned_country(country) is expected

    def test_empty(self):
        assert lib.is_sanctioned_country("") is False


class TestSanctionedEntity:
    def test_sdn_hit_exact(self):
        assert lib.is_sanctioned_entity("Wagner Group") is True

    def test_sdn_miss(self):
        assert lib.is_sanctioned_entity("ACME Industrial Imports") is False

    def test_sdn_hit_in_snippet(self):
        # 在 snippet 中命中也能识别
        assert lib.is_sanctioned_entity("Some Company",
                                         "We work with Hezbollah Procurement Unit") is True


class TestDualUse:
    def test_octg_re_export_hit(self):
        assert lib.has_dual_use_term("OCTG for re-export to Iran") is True

    def test_no_hit(self):
        assert lib.has_dual_use_term("Normal oilfield procurement") is False


class TestFraud:
    def test_advance_payment_hit(self):
        hits = lib.has_fraud_term("100% advance payment to personal account")
        assert len(hits) >= 1

    def test_clean(self):
        assert lib.has_fraud_term("standard LC at 30/70") == []


# ================================================================
# 2. customer type detection
# ================================================================

class TestCustomerType:
    def test_manufacturer(self):
        assert lib.detect_customer_type("We are a manufacturing company") == "Manufacturer"

    def test_distributor(self):
        assert lib.detect_customer_type("Top distributor of steel pipes") == "Distributor"

    def test_epc(self):
        assert lib.detect_customer_type("Major EPC contractor") == "EPC"

    def test_oem(self):
        assert lib.detect_customer_type("OEM supplier of valves") == "OEM"

    def test_end_user(self):
        assert lib.detect_customer_type("Oilfield operator in NEOM") == "End User"

    def test_trader(self):
        assert lib.detect_customer_type("Import export trading house") == "Trader"

    def test_unknown(self):
        assert lib.detect_customer_type("We sell things") == "Unknown"


# ================================================================
# 3. Schema validation
# ================================================================

class TestSchema:
    def test_missing_buyer_name(self):
        with pytest.raises(lib.InvalidBuyerRecord):
            lib.assert_buyer_shape({"country": "US"})

    def test_missing_country(self):
        with pytest.raises(lib.InvalidBuyerRecord):
            lib.assert_buyer_shape({"importer_name": "Acme"})

    def test_valid(self):
        lib.assert_buyer_shape({"importer_name": "Acme", "country": "US"})


# ================================================================
# 4. 5-dim scoring
# ================================================================

class TestScoringD1Real:
    """D1 — 公司真实性（25）"""

    def test_full_score_with_email_linkedin(self):
        buyer = {
            "importer_name": "Acme", "country": "US",
            "contact_email": "buyers@acme.com",
            "linkedin": "https://linkedin.com/company/acme",
        }
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D1_real"]["score"] == 25

    def test_deducted_no_email(self):
        buyer = {"importer_name": "Acme", "country": "US",
                  "linkedin": "https://linkedin.com/company/acme"}
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D1_real"]["score"] < 25
        assert "contact_email" in r["scoring"]["D1_real"]["missing"]

    def test_free_email_deducted(self):
        buyer = {"importer_name": "Acme", "country": "US",
                  "contact_email": "buyer@gmail.com",
                  "linkedin": "https://linkedin.com/company/acme"}
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D1_real"]["score"] == 18  # 5 + 5 + 8 = 18


class TestScoringD2Size:
    def test_size_and_revenue_signal(self):
        buyer = {"importer_name": "Big Co", "country": "US",
                  "snippet": "We employ 5000 workers with USD 800M revenue in industry"}
        r = lib.evaluate_buyer(buyer)
        d2 = r["scoring"]["D2_size"]["score"]
        assert d2 >= 15

    def test_no_signals(self):
        buyer = {"importer_name": "Tiny Co", "country": "US",
                  "snippet": "Just a small shop"}
        r = lib.evaluate_buyer(buyer)
        d2 = r["scoring"]["D2_size"]["score"]
        assert d2 <= 10  # 只靠 industry_signal


class TestScoringD3Type:
    def test_high_quality_type(self):
        buyer = {"importer_name": "Mfg Co", "country": "US",
                  "snippet": "Leading manufacturing plant"}
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D3_type"]["score"] == 15
        assert r["scoring"]["D3_type"]["customer_type"] == "Manufacturer"

    def test_low_quality_type(self):
        buyer = {"importer_name": "Trader Co", "country": "US",
                  "snippet": "Trading company for import export"}
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D3_type"]["score"] <= 5


class TestScoringD5Risk:
    def test_clean_buyer_full_risk_score(self):
        buyer = {"importer_name": "Clean Inc", "country": "US",
                  "snippet": "Standard procurement"}
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D5_risk"]["score"] == 15

    def test_sanctioned_country_zero_risk_score(self):
        buyer = {"importer_name": "X", "country": "Iran",
                  "snippet": "buying stuff"}
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D5_risk"]["score"] == 0

    def test_fraud_signal_zero_risk_score(self):
        buyer = {"importer_name": "Y", "country": "US",
                  "snippet": "100% advance payment to personal account OK"}
        r = lib.evaluate_buyer(buyer)
        assert r["scoring"]["D5_risk"]["score"] == 0


class TestScoringGrade:
    def test_grade_a(self):
        buyer = {
            "importer_name": "Premium Mfg", "country": "US",
            "contact_email": "buyer@premium-mfg.com",
            "linkedin": "https://linkedin.com/company/premium-mfg",
            "snippet": "50,000 employees in manufacturing, USD 5B revenue, industry leader.",
            "usd_history": 10000000,
        }
        r = lib.evaluate_buyer(buyer)
        assert r["company_grade"] == "A", r

    def test_grade_d_min(self):
        buyer = {"importer_name": "X", "country": "US"}  # 几乎无信息
        r = lib.evaluate_buyer(buyer)
        assert r["company_grade"] in ("D", "C"), r["scoring"]["total"]

    def test_grade_thresholds(self):
        # 验证阈值表正确
        assert lib.GRADE_THRESHOLDS[0][0] == 90
        assert lib.GRADE_THRESHOLDS[1][0] == 70
        assert lib.GRADE_THRESHOLDS[2][0] == 50


# ================================================================
# 5. Compliance + Routing
# ================================================================

class TestComplianceAndRouting:
    def test_sanctioned_country_halts(self):
        buyer = {"importer_name": "X", "country": "North Korea"}
        r = lib.evaluate_buyer(buyer)
        assert r["compliance"]["passed"] is False
        assert r["recommendation"]["action"] == "halt"
        assert "hlzd-trade-compliance" in r["recommendation"]["next_skill"]

    def test_sdn_hit_halts(self):
        buyer = {"importer_name": "Hezbollah Procurement", "country": "Lebanon"}
        r = lib.evaluate_buyer(buyer)
        assert r["compliance"]["passed"] is False
        assert r["recommendation"]["action"] == "halt"

    def test_fraud_signal_halts(self):
        buyer = {"importer_name": "Y", "country": "US",
                  "snippet": "100% advance to personal account"}
        r = lib.evaluate_buyer(buyer)
        assert r["recommendation"]["action"] == "halt"
        assert any(fraud in r["compliance"]["fraud_terms_detected"] for fraud in ["100% advance"])

    def test_clean_grade_a_to_outreach(self):
        buyer = {
            "importer_name": "ABC Corp", "country": "USA",
            "contact_email": "buyer@abc.com",
            "linkedin": "https://linkedin.com/company/abc",
            "snippet": "Leading manufacturing with 3000 employees, USD 800M revenue.",
        }
        r = lib.evaluate_buyer(buyer)
        assert r["compliance"]["passed"]
        if r["company_grade"] == "A":
            assert r["recommendation"]["action"] == "outreach_24h"
            assert r["recommendation"]["next_skill"] == "hlzd-cold-outreach"


# ================================================================
# 6. batch evaluate
# ================================================================

class TestBatchEvaluate:
    def test_mixed_quality(self):
        buyers = [
            {"importer_name": "Good Co", "country": "USA", "contact_email": "a@good.com",
             "linkedin": "https://linkedin.com/company/good",
             "snippet": "Manufacturing with 5000 workers, USD 1B revenue, industry leader.",
             "usd_history": 5000000},
            {"importer_name": "Hezbollah", "country": "Lebanon"},  # SDN
            {"importer_name": "Tiny", "country": "US"},  # D
        ]
        r = lib.evaluate_many(buyers)
        assert r["evaluated"] == 3
        assert r["failed"] == 0
        assert r["halt_recommended"] == 1
        assert "A" in r["by_grade"]  # at least one A or B
        assert r["by_grade"]["D"] >= 1

    def test_errors_collected(self):
        buyers = [
            {"importer_name": "Good Co", "country": "USA"},
            {"country": "US"},  # missing name
        ]
        r = lib.evaluate_many(buyers)
        assert r["evaluated"] == 1
        assert r["failed"] == 1

    def test_empty_input(self):
        r = lib.evaluate_many([])
        assert r["evaluated"] == 0
        assert r["results"] == []


# ================================================================
# 7. Source adapters
# ================================================================

class TestLinkedInExtract:
    def test_extract_company_url(self):
        text = "Find us at https://www.linkedin.com/company/acme-inc"
        assert linkedin.extract_linkedin(text) == "https://linkedin.com/company/acme-inc"

    def test_no_match(self):
        assert linkedin.extract_linkedin("just a normal text") is None

    def test_handles_none(self):
        assert linkedin.extract_linkedin(None) is None

    def test_infer_handle(self):
        url, handle = linkedin.infer_linkedin_from_name("Acme Corp LLC", "US")
        assert "acme-corp" in handle  # limited dedup


class TestWhoisExtract:
    def test_extract(self):
        text = "Visit https://acme.example.com for catalog"
        url = whois.extract_website(text)
        assert url and "acme.example.com" in url

    def test_skip_linkedin(self):
        text = "https://linkedin.com/company/x"
        assert whois.extract_website(text) is None

    def test_handles_none(self):
        assert whois.extract_website(None) is None

    def test_infer_email_domain(self):
        assert whois.infer_email_domain("https://acme.com/about") == "acme.com"


class TestSanctionsList:
    def test_static_names_present(self):
        names = sanctions.OFAC_SDN_STATIC_NAMES
        assert len(names) >= 20
        assert "Wagner Group" in names
        assert "Hezbollah" in names


# ================================================================
# 8. End-to-end schema
# ================================================================

class TestEndToEndSchema:
    def test_output_shape(self):
        buyers = [
            {"importer_name": "ABC", "country": "US", "contact_email": "a@b.com",
             "linkedin": "https://linkedin.com/company/abc",
             "snippet": "30000 employees in industry, USD 1B revenue."},
        ]
        r = lib.evaluate_many(buyers)
        for k in ("$schema", "evaluated", "failed", "halt_recommended",
                   "by_grade", "results", "errors"):
            assert k in r, f"missing top-level {k}"

        # 每个 result 必含字段
        res = r["results"][0]
        for k in ("importer_name", "country", "company_score", "company_grade",
                   "scoring", "compliance", "recommendation"):
            assert k in res, f"missing result.{k}"
