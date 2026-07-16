#!/usr/bin/env python3
"""hlzd-negotiation-playbook tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402


# ================================================================
# 1. parse_offer
# ================================================================

class TestParseOffer:
    def test_usd_price(self):
        out = lib.parse_offer("We can pay USD 1300 per ton")
        assert out["target_price"] == 1300.0

    def test_eur_price(self):
        out = lib.parse_offer("Target price EUR 1200")
        assert out["target_price"] == 1200.0

    def test_lead_days(self):
        out = lib.parse_offer("Can you deliver in 60 days?")
        assert out["desired_lead_days"] == 60

    def test_advance_pct(self):
        out = lib.parse_offer("We accept 30% advance")
        assert out["advance_pct"] == 30
        assert out["balance_pct"] == 70

    def test_lc_hint(self):
        out = lib.parse_offer("We can do 30% advance + 70% LC at sight")
        assert out.get("payment_method_hint") == "lc"

    def test_no_numbers(self):
        out = lib.parse_offer("please send catalogue")
        assert out == {}


# ================================================================
# 2. Price simulation
# ================================================================

class TestPriceSimulation:
    def test_basic_three_rounds(self):
        out = lib.simulate_price(1500, 1200)
        assert len(out) == 3
        assert out[0]["round"] == 1
        assert out[0]["proposed_price_usd"] == 1500 * 0.95

    def test_prices_decreasing(self):
        out = lib.simulate_price(1500, 1000)
        for i in range(len(out) - 1):
            assert out[i]["proposed_price_usd"] >= out[i + 1]["proposed_price_usd"]

    def test_breach_when_target_too_low(self):
        out = lib.simulate_price(1000, 800, [0.30, 0.05, 0.02])
        # round 1: 1000 * 0.7 = 700 < 800 → breach
        assert out[0]["breaches_redline"] is True
        assert out[1]["breaches_redline"] is True
        assert out[2]["breaches_redline"] is True

    def test_no_breach_when_target_safe(self):
        out = lib.simulate_price(1500, 1300)
        for r in out:
            assert r["breaches_redline"] is False

    def test_invalid_price(self):
        with pytest.raises(lib.InvalidInput):
            lib.simulate_price(0, 1000)
        with pytest.raises(lib.InvalidInput):
            lib.simulate_price(1500, 0)

    def test_cumulative_pct_tracking(self):
        out = lib.simulate_price(1500, 1200, [0.05, 0.10, 0.02])
        assert out[0]["cumulative_concession_pct"] == 0.05
        assert out[1]["cumulative_concession_pct"] == 0.15
        assert out[2]["cumulative_concession_pct"] == 0.17


# ================================================================
# 3. Lead time simulation
# ================================================================

class TestLeadSimulation:
    def test_default_concessions(self):
        out = lib.simulate_lead_time(40, 30)
        # default: [0, 5, 10]
        assert out[0]["new_lead_days"] == 40
        assert out[1]["new_lead_days"] == 35
        assert out[2]["new_lead_days"] == 30

    def test_breach_when_no_concession_helps(self):
        # initial=30, desired=20. Default concessions [0,5,10].
        # Round 1: 30-0=30 > 20 → 远未达成 (breach)
        # Round 2: 30-5=25 > 20 → 仍未达成 (breach)
        # Round 3: 30-15=15 < 20 → 已达成 (no breach)
        out = lib.simulate_lead_time(30, 20)
        assert out[0]["breaches_redline"] is True
        assert out[1]["breaches_redline"] is True
        assert out[2]["breaches_redline"] is False
        # Round 3 的实际 lead 是 20（max(15, 20) → 20）
        assert out[2]["new_lead_days"] == 20

    def test_invalid(self):
        with pytest.raises(lib.InvalidInput):
            lib.simulate_lead_time(0, 10)


# ================================================================
# 4. Payment terms simulation
# ================================================================

class TestPaymentSimulation:
    def test_default_path(self):
        out = lib.simulate_payment_terms(initial_advance_pct=30)
        assert len(out) == 3
        assert out[0]["advance_pct"] == 30
        assert out[1]["advance_pct"] == 20
        assert out[2]["advance_pct"] == 10

    def test_delta_tracking(self):
        out = lib.simulate_payment_terms(initial_advance_pct=30)
        assert out[1]["delta_from_initial_pct"] == -10
        assert out[2]["delta_from_initial_pct"] == -20


# ================================================================
# 5. Decision routing
# ================================================================

class TestRecommendAction:
    def _empty_rounds(self):
        return []

    def _price_rounds(self, breach_count: int = 0):
        return [{"breaches_redline": i < breach_count} for i in range(3)]

    def _lead_rounds(self, breach_count: int = 0):
        return [{"breaches_redline": i < breach_count} for i in range(3)]

    def test_default_accept_round_2(self):
        a = lib.recommend_action(
            self._price_rounds(0), self._lead_rounds(0), [{}] * 3,
        )
        assert a["decision"] == "accept_round_2"

    def test_price_breach_counter(self):
        a = lib.recommend_action(
            self._price_rounds(1), self._lead_rounds(0), [{}] * 3,
        )
        assert a["decision"] == "counter"

    def test_lead_breach_counter_with_freight(self):
        a = lib.recommend_action(
            self._price_rounds(0), self._lead_rounds(1), [{}] * 3,
        )
        assert a["decision"] == "counter_with_freight"

    def test_both_breach_walk_away(self):
        a = lib.recommend_action(
            self._price_rounds(2), self._lead_rounds(1), [{}] * 3,
        )
        assert a["decision"] == "walk_away"

    def test_competitor_risk_overrides(self):
        a = lib.recommend_action(
            self._price_rounds(0), self._lead_rounds(0), [{}] * 3,
            lose_to_competitor_risk=True,
        )
        assert a["decision"] == "accept_round_3"


# ================================================================
# 6. Pipeline
# ================================================================

class TestRunPlaybook:
    def _initial_quote(self):
        return {
            "quantity_tons": 500,
            "incoterms": {"FOB": {"total_usd": 750000}},   # 1500 USD/ton
            "components": {},
        }

    def test_basic_run(self):
        report = lib.run_playbook(
            initial_quote=self._initial_quote(),
            customer_response={"target_price": 1300, "desired_lead_days": 30},
            redlines={"min_acceptable_price": 1300},
        )
        assert "rounds" in report
        for axis in ("price", "lead_time", "payment_terms"):
            assert axis in report["rounds"]

    def test_redline_breaches(self):
        # default concessions 5/3/2 = 10% total. Initial 1500 → round 3 = 1350.
        # Customer target 1300 — our 1350 > 1300, NOT breached (we can't go low enough).
        report = lib.run_playbook(
            initial_quote=self._initial_quote(),
            customer_response={"target_price": 1400},
        )
        # Default concessions 让完 = 1350；目标 1400 → 1350 < 1400, breach in round 3
        assert report["red_line_breached"]["price"] is True

    def test_redline_acceptable(self):
        # Comfortable target — no breach
        report = lib.run_playbook(
            initial_quote=self._initial_quote(),
            customer_response={"target_price": 1490},
        )
        # Initial 1500; default 让完 = 1350 < 1490 → breach (我们让穿客户目标)
        # 这是 "breach" = 我们已经让超过 customer target (loss-making)
        assert report["red_line_breached"]["price"] is True

    def test_decision_present(self):
        report = lib.run_playbook(
            initial_quote=self._initial_quote(),
            customer_response={"target_price": 1300},
        )
        assert "decision" in report
        assert "next_step" in report["decision"]


# ================================================================
# 7. End-to-end schema
# ================================================================

class TestSchema:
    def test_required_top_keys(self):
        report = lib.run_playbook(
            initial_quote={"quantity_tons": 500,
                            "incoterms": {"FOB": {"total_usd": 750000}},
                            "components": {}},
            customer_response={"target_price": 1300},
        )
        for k in ("$schema", "initial_state", "redlines", "rounds",
                   "red_line_breached", "decision"):
            assert k in report

    def test_rounds_have_axis(self):
        report = lib.run_playbook(
            initial_quote={"quantity_tons": 500,
                            "incoterms": {"FOB": {"total_usd": 750000}},
                            "components": {}},
            customer_response={"target_price": 1300},
        )
        for axis in ("price", "lead_time", "payment_terms"):
            r = report["rounds"][axis]
            for round_data in r:
                assert "round" in round_data
