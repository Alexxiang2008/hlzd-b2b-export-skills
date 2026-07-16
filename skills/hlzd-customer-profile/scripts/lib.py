#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hlzd-customer-profile — 客户 5 维评级（A/B/C/D）+ 4 层字段模型校验。

v0.1.0 仅交付可测核心算法；v0.2 计划对接真实数据源（CRM / 海关）。
"""
from __future__ import annotations
from typing import Any, Dict, List


def score_customer(profile: Dict[str, Any]) -> Dict[str, Any]:
    """5 维评级：basic / trade / behavior / finance / risk → A/B/C/D."""
    dims = {
        "basic": _score_basic(profile.get("company", {})),
        "trade": _score_trade(profile.get("trade_history", {})),
        "behavior": _score_behavior(profile.get("behavior", {})),
        "finance": _score_finance(profile.get("finance", {})),
        "risk": _score_risk(profile.get("risk_flags", [])),
    }
    total = sum(dims.values())
    grade = _grade(total)
    return {"dimensions": dims, "total": total, "grade": grade}


def _score_basic(c: Dict[str, Any]) -> int:
    s = 0
    if c.get("registered"): s += 5
    if c.get("employees", 0) >= 50: s += 5
    if c.get("years_in_business", 0) >= 5: s += 5
    if c.get("website_verified"): s += 3
    if c.get("linkedin_presence"): s += 2
    return min(s, 20)


def _score_trade(t: Dict[str, Any]) -> int:
    s = 0
    s += min(int(t.get("total_orders", 0)) // 5, 10)
    s += min(int(t.get("total_value_usd", 0)) // 100000, 10)
    return min(s, 20)


def _score_behavior(b: Dict[str, Any]) -> int:
    s = 0
    if b.get("reply_rate_30d", 0) >= 0.5: s += 7
    if b.get("meeting_count_90d", 0) >= 3: s += 7
    if b.get("rfq_count_180d", 0) >= 5: s += 6
    return min(s, 20)


def _score_finance(f: Dict[str, Any]) -> int:
    s = 0
    if f.get("credit_check_passed"): s += 10
    if f.get("payment_on_time_rate", 0) >= 0.9: s += 7
    if not f.get("overdue_amount", 0): s += 3
    return min(s, 20)


def _score_risk(flags: List[str]) -> int:
    if any(f in flags for f in ("sanctioned_country", "ofac_match")):
        return 0
    if "fraud_signal" in flags:
        return 5
    return 20


def _grade(total: int) -> str:
    if total >= 85: return "A"
    if total >= 70: return "B"
    if total >= 50: return "C"
    return "D"


def validate_profile_schema(profile: Dict[str, Any]) -> List[str]:
    """校验 4 层字段模型必需键。返回缺失键列表。"""
    required = {
        "company": ["name", "country"],
        "trade_history": [],
        "behavior": [],
        "finance": [],
        "risk_flags": [],
    }
    missing: List[str] = []
    for layer, keys in required.items():
        if layer not in profile:
            missing.append(f"layer:{layer}")
            continue
        for k in keys:
            if k not in profile[layer]:
                missing.append(f"{layer}.{k}")
    return missing
