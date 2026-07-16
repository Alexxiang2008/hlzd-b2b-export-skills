#!/usr/bin/env python3
"""hlzd-quotation-gen tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402


SKU_BASE = {"sku": "TEST", "currency": "USD", "unit_price_per_ton": 1000}


# ================================================================
# FX / 单位换算
# ================================================================

class TestFXConversion:
    def test_usd_to_usd(self):
        assert lib._unit_price_in_usd(1000, "USD") == 1000.0

    def test_eur_to_usd(self):
        # 920 EUR = 1000 USD (rate 0.92)
        assert lib._unit_price_in_usd(920, "EUR") == pytest.approx(1000.0)

    def test_unsupported_currency_raises(self):
        with pytest.raises(lib.InvalidInput):
            lib._unit_price_in_usd(1000, "XYZ")

    def test_cny_to_usd(self):
        # 7200 CNY = 1000 USD (rate 7.20)
        assert lib._unit_price_in_usd(7200, "CNY") == pytest.approx(1000.0)


# ================================================================
# Ocean freight
# ================================================================

class TestOceanFreight:
    @pytest.mark.parametrize("country,region", [
        ("ae", "middle_east"),
        ("NG", "west_africa"),
        ("KE", "east_africa"),
        ("PK", "south_asia"),
        ("us", "north_america_west"),
        ("br", "south_america_east"),
        ("de", "europe"),
        ("au", "oceania"),
    ])
    def test_region_resolution(self, country, region):
        cost = lib._estimate_ocean_freight_usd(country)
        expected = lib.OCEAN_FREIGHT_USD_BY_REGION[region]
        assert cost == expected


# ================================================================
# calculate_quote core
# ================================================================

class TestCalculateQuote:
    def test_basic_fob(self):
        q = lib.calculate_quote(
            sku=SKU_BASE, quantity_tons=100,
            target_country="AE", incoterm="FOB",
        )
        assert "FOB" in q["incoterms"]
        assert q["incoterms"]["FOB"]["total_usd"] > 0

    def test_fob_less_than_cif(self):
        q = lib.calculate_quote(
            sku=SKU_BASE, quantity_tons=100,
            target_country="US", incoterm="FOB",
        )
        assert q["incoterms"]["FOB"]["total_usd"] < q["incoterms"]["CIF"]["total_usd"]

    def test_fob_less_than_ddp(self):
        q = lib.calculate_quote(
            sku=SKU_BASE, quantity_tons=100,
            target_country="DE", incoterm="FOB",
        )
        assert q["incoterms"]["FOB"]["total_usd"] < q["incoterms"]["DDP"]["total_usd"]

    def test_currency_conversion(self):
        q_eur = lib.calculate_quote(
            sku={**SKU_BASE, "currency": "EUR", "unit_price_per_ton": 920},
            quantity_tons=100, target_country="AE", target_currency="EUR",
        )
        # FOB 应比 USD 版本近似相等
        q_usd = lib.calculate_quote(
            sku={**SKU_BASE, "currency": "USD", "unit_price_per_ton": 1000},
            quantity_tons=100, target_country="AE",
        )
        ratio = q_eur["incoterms"]["FOB"]["total_usd"] / q_usd["incoterms"]["FOB"]["total_usd"]
        # 同一 base USD，二者应一致
        assert ratio == pytest.approx(1.0, abs=0.01)

    def test_profit_healthy_range(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE")
        assert 0.15 <= q["profit_realized"]["ratio"] <= 0.25

    def test_low_margin_warning(self):
        # margin 设 5% → 实际 ratio 会因 rebate 等 > 5%，但如果 rebake / 其他成本吃光就低
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE", profit_margin=0.05)
        # ratio 应该 < 0.10（健康值）触发警告
        assert q["profit_realized"]["ratio"] < 0.10
        assert q["profit_realized"]["warning"] is not None

    def test_high_margin_advisory(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE", profit_margin=0.35)
        # ratio > 0.25 → advisory
        assert q["profit_realized"]["ratio"] > 0.25
        assert "HIGH" in q["profit_realized"]["health"]

    def test_invalid_quantity(self):
        with pytest.raises(lib.InvalidInput):
            lib.calculate_quote(sku=SKU_BASE, quantity_tons=0,
                                  target_country="AE")

    def test_negative_margin(self):
        with pytest.raises(lib.InvalidInput):
            lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE", profit_margin=-0.1)

    def test_excessive_margin(self):
        with pytest.raises(lib.InvalidInput):
            lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE", profit_margin=0.8)


# ================================================================
# Payment terms
# ================================================================

class TestPaymentTerms:
    def test_normal_country_advance(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE")
        assert "30% T/T advance" in q["payment_terms"]["primary"]

    def test_high_risk_country(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="Iran")
        assert "100% T/T in advance" in q["payment_terms"]["primary"]

    def test_thin_margin_uses_lc(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE", profit_margin=0.05)
        assert "L/C" in q["payment_terms"]["primary"]


# ================================================================
# Schema
# ================================================================

class TestSchema:
    def test_required_top_keys(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE")
        for k in ("$schema", "sku", "quantity_tons", "target_country",
                   "currency", "components", "incoterms",
                   "profit_realized", "payment_terms"):
            assert k in q

    def test_components_breakdown(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE")
        c = q["components"]
        for k in ("factory_unit_price_usd", "factory_cost_usd",
                   "packaging_cost_usd", "export_rebate_usd",
                   "ocean_freight_usd", "insurance_usd",
                   "target_duty_rate", "target_duty_usd",
                   "customs_clearance_fee_usd"):
            assert k in c

    def test_incoterms_includes_all(self):
        q = lib.calculate_quote(sku=SKU_BASE, quantity_tons=100,
                                  target_country="AE")
        for term in ("FOB", "CIF", "DDP"):
            assert term in q["incoterms"]
            assert "total_usd" in q["incoterms"][term]
            assert "unit_price_usd_per_ton" in q["incoterms"][term]
