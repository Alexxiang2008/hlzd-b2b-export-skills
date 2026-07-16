#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hlzd-customer-profile lib 测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import score_customer, validate_profile_schema, _grade  # noqa: E402


def test_grade_a_top_customer():
    p = {
        "company": {"registered": True, "employees": 200, "years_in_business": 10,
                    "website_verified": True, "linkedin_presence": True},
        "trade_history": {"total_orders": 60, "total_value_usd": 1500000},
        "behavior": {"reply_rate_30d": 0.8, "meeting_count_90d": 5, "rfq_count_180d": 8},
        "finance": {"credit_check_passed": True, "payment_on_time_rate": 0.95},
        "risk_flags": [],
    }
    r = score_customer(p)
    assert r["grade"] == "A", f"expected A, got {r['grade']} (total={r['total']})"
    assert r["total"] >= 85


def test_grade_d_sanctioned():
    p = {
        "company": {"registered": True},
        "trade_history": {},
        "behavior": {},
        "finance": {},
        "risk_flags": ["sanctioned_country"],
    }
    r = score_customer(p)
    assert r["grade"] == "D"
    assert r["dimensions"]["risk"] == 0


def test_missing_layer():
    errs = validate_profile_schema({"company": {"name": "X", "country": "US"}})
    assert any("layer:" in e for e in errs)
    assert any("trade_history" in e for e in errs)


def test_full_profile_no_missing():
    p = {
        "company": {"name": "Acme", "country": "US"},
        "trade_history": {},
        "behavior": {},
        "finance": {},
        "risk_flags": [],
    }
    assert validate_profile_schema(p) == []


def test_grade_thresholds():
    assert _grade(85) == "A"
    assert _grade(70) == "B"
    assert _grade(50) == "C"
    assert _grade(30) == "D"
