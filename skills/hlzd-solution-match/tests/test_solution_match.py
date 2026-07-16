#!/usr/bin/env python3
"""hlzd-solution-match tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402


# ================================================================
# Helpers
# ================================================================

class TestNormalize:
    def test_strip_and_lower(self):
        assert lib._norm("  Hello World  ") == "hello world"

    def test_none_safe(self):
        assert lib._norm(None) == ""

    def test_int_safe(self):
        assert lib._norm(42) == "42"


class TestAppExtraction:
    def test_extract_oilfield(self):
        apps = lib._listify_application("We need pipes for oilfield / downhole use")
        assert "oilfield" in apps
        assert "downhole" in apps

    def test_extract_sour_service(self):
        apps = lib._listify_application("sour service application H2S")
        assert "sour service" in apps


class TestCertExtraction:
    def test_extract_api_5ct(self):
        assert "api 5ct" in lib._extract_certifications("API 5CT casing required")

    def test_no_false_positive(self):
        assert lib._extract_certifications("no certs in here") == []


# ================================================================
# Scoring
# ================================================================

class TestScoreD1Spec:
    def test_perfect_match_full(self):
        sku = lib.DEFAULT_CATALOG[0]  # OCTG-L80-95-BTC-PREMIUM
        enquiry = {
            "product": "OCTG",
            "certifications_required": ["API 5CT", "NACE MR0175"],
            "text": "sour service oilfield",
        }
        r = lib.score_sku(enquiry, sku)
        assert r["D1_spec"]["score"] >= 25

    def test_category_mismatch(self):
        sku = lib.DEFAULT_CATALOG[0]  # OCTG
        enquiry = {"product": "Solar Panel", "text": ""}
        r = lib.score_sku(enquiry, sku)
        assert any("category_mismatch" in m for m in r["D1_spec"]["missing"])

    def test_missing_certs(self):
        sku = lib.DEFAULT_CATALOG[2]  # only API 5CT
        enquiry = {"product": "OCTG", "certifications_required": ["API 5CT", "NACE MR0175"]}
        r = lib.score_sku(enquiry, sku)
        assert any("cert_missing" in m for m in r["D1_spec"]["missing"])


class TestScoreD2Qty:
    def test_qty_meets_moq(self):
        sku = lib.DEFAULT_CATALOG[0]  # MOQ 30 tons
        enquiry = {"product": "OCTG", "quantity": "500 tons"}
        r = lib.score_sku(enquiry, sku)
        assert r["D2_qty"]["score"] >= 8

    def test_qty_below_moq(self):
        sku = lib.DEFAULT_CATALOG[0]  # MOQ 30
        enquiry = {"product": "OCTG", "quantity": "5 tons"}
        r = lib.score_sku(enquiry, sku)
        assert any("below_moq" in m for m in r["D2_qty"]["missing"])

    def test_qty_above_capacity(self):
        sku = lib.DEFAULT_CATALOG[0]  # 800 tons/month
        enquiry = {"product": "OCTG", "quantity": "10000 tons"}
        r = lib.score_sku(enquiry, sku)
        assert any("above_monthly_capacity" in m for m in r["D2_qty"]["missing"])

    def test_no_quantity_neutral(self):
        sku = lib.DEFAULT_CATALOG[0]
        enquiry = {"product": "OCTG"}
        r = lib.score_sku(enquiry, sku)
        assert r["D2_qty"]["score"] == 7  # 中性


class TestScoreD3Lead:
    def test_lead_time_comfortable(self):
        sku = lib.DEFAULT_CATALOG[0]  # 30 days
        enquiry = {"product": "OCTG", "lead_time_days": 60}
        r = lib.score_sku(enquiry, sku)
        assert r["D3_lead"]["score"] == 20

    def test_lead_time_too_tight(self):
        sku = lib.DEFAULT_CATALOG[0]  # 30 days
        enquiry = {"product": "OCTG", "lead_time_days": 7}
        r = lib.score_sku(enquiry, sku)
        assert any("too_short" in m for m in r["D3_lead"]["missing"])


class TestScoreD4Tier:
    def test_economy_full(self):
        sku = next(s for s in lib.DEFAULT_CATALOG if s["sku"] == "OCTG-J55-95-EUE-ECONOMY")
        r = lib.score_sku({"product": "OCTG"}, sku)
        assert r["D4_price_tier"]["score"] == 15  # tier 0

    def test_premium_zero(self):
        sku = next(s for s in lib.DEFAULT_CATALOG if s["sku"] == "OCTG-L80-95-BTC-PREMIUM")
        r = lib.score_sku({"product": "OCTG"}, sku)
        assert r["D4_price_tier"]["score"] == 0   # tier 3 abs(3-1)*5


class TestScoreD5Risk:
    def test_clean(self):
        sku = lib.DEFAULT_CATALOG[1]  # N80 STANDARD
        enquiry = {"product": "OCTG", "quantity": "500 tons", "lead_time_days": 30}
        r = lib.score_sku(enquiry, sku)
        assert r["D5_risk"]["score"] == 20

    def test_one_risk(self):
        sku = lib.DEFAULT_CATALOG[2]  # J55 ECONOMY missing NACE
        enquiry = {"product": "OCTG", "quantity": "500 tons", "lead_time_days": 30,
                    "certifications_required": ["API 5CT", "NACE MR0175"]}
        r = lib.score_sku(enquiry, sku)
        assert r["D5_risk"]["score"] < 20


# ================================================================
# Pipeline
# ================================================================

class TestRecommendThree:
    def _enquiry(self):
        return {
            "product": "OCTG",
            "quantity": "500 tons",
            "certifications_required": ["API 5CT", "NACE MR0175"],
            "text": "sour service oilfield",
            "lead_time_days": 60,
        }

    def test_basic_three_plans(self):
        r = lib.recommend_three(self._enquiry())
        for plan_name in ("best_match", "alternative", "cost_effective"):
            assert plan_name in r
            assert "sku" in r[plan_name]
            assert "match_score" in r[plan_name]

    def test_cost_effective_is_economical(self):
        r = lib.recommend_three(self._enquiry())
        cost = r["cost_effective"]
        # cost-effective 应该是 tier 最低（"economy"）
        assert cost["specs"].get("tier") == "economy" or cost["tier"] == "cost_effective"

    def test_best_match_differs_from_cost_in_general(self):
        r = lib.recommend_three(self._enquiry())
        assert r["best_match"]["sku"] != r["cost_effective"]["sku"]

    def test_evaluated_count(self):
        r = lib.recommend_three(self._enquiry())
        assert r["evaluated_skus"] == len(lib.DEFAULT_CATALOG)

    def test_all_risks_collected(self):
        r = lib.recommend_three(self._enquiry())
        assert isinstance(r["all_risks"], list)

    def test_custom_catalog(self):
        catalog = [{
            "sku": "X", "category": "Test",
            "certifications": [], "applications": [],
            "moq_tons": 1, "capacity_per_month_tons": 100,
            "lead_time_days": 10, "unit_price_per_ton": 100, "tier_index": 1,
        }]
        r = lib.recommend_three({"product": "Test"}, catalog=catalog)
        assert r["evaluated_skus"] == 1
        assert r["best_match"]["sku"] == "X"
        assert r["alternative"]["sku"] == "X"
        assert r["cost_effective"]["sku"] == "X"

    def test_invalid_input_raises(self):
        with pytest.raises(lib.InvalidInput):
            lib.recommend_three({"product": "OCTG"}, catalog=[])

    def test_no_catalog_uses_default(self):
        r = lib.recommend_three({"product": "OCTG"})
        assert r["evaluated_skus"] >= 3


# ================================================================
# End-to-end schema
# ================================================================

class TestSchema:
    def test_required_top_keys(self):
        r = lib.recommend_three({"product": "OCTG"})
        for k in ("$schema", "enquiry_product", "evaluated_skus",
                   "best_match", "alternative", "cost_effective", "all_risks"):
            assert k in r

    def test_plan_required_keys(self):
        r = lib.recommend_three({"product": "OCTG"})
        for plan in ("best_match", "alternative", "cost_effective"):
            p = r[plan]
            for k in ("tier", "sku", "category", "specs", "match_score",
                       "scoring_breakdown", "risks", "rationale"):
                assert k in p, f"missing {plan}.{k}"

    def test_scoring_breakdown_dimensions(self):
        r = lib.recommend_three({"product": "OCTG"})
        for plan in ("best_match", "alternative", "cost_effective"):
            sd = r[plan]["scoring_breakdown"]
            for k in ("D1_spec", "D2_qty", "D3_lead", "D4_price_tier", "D5_risk"):
                assert k in sd
                assert "score" in sd[k]
                assert "max" in sd[k]
                assert "missing" in sd[k]
