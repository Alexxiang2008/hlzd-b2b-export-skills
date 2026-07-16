"""hlzd-quotation-gen shared library.

输入：产品 (HS + specs) + 数量 + 目的港 + 贸易术语 (FOB / CIF / DDP)
输出：3 套报价（FOB / CIF / DDP）+ 利润预警 + 账期建议

设计：
- 成本拆解：factory cost + packaging + inland + ocean + insurance + customs + duty
- 汇率 stub（v0.1 占位）；实际用 FX API
- 利润校验：<10% 警告 / 10-15% 偏低 / 15-25% OK / >25% 过高（可能失去商机）
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-quotation-gen") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# 错误归类
# ================================================================

class QuotationError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-quotation-gen",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


class InvalidInput(QuotationError):
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


# ================================================================
# 静态默认值
# ================================================================

# v0.1 汇率 stub：实际接 FX API（Open Exchange Rates / 国家外管局）
FX_RATES_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "CNY": 7.20,
    "AED": 3.67,
    "SAR": 3.75,
    "ZAR": 18.50,
    "BRL": 5.10,
    "MXN": 17.20,
    "GBP": 0.78,
}

# 集装箱海运成本估算（v0.1 stub，单位 USD / 20GP）
OCEAN_FREIGHT_USD_BY_REGION: Dict[str, float] = {
    "middle_east": 1200,    # UAE / Saudi
    "west_africa": 2400,
    "east_africa": 1800,
    "south_asia": 1300,
    "north_america_west": 2200,  # US West Coast
    "north_america_east": 2600,  # US East Coast
    "south_america_east": 3400,  # Brazil / Argentina
    "europe": 1400,
    "oceania": 1700,
    "southeast_asia": 900,
}

# 默认海运保险：0.3% of CIF value
INSURANCE_RATE = 0.003

# 默认出口退税（中国）：9% / 13%（v0.1 取平均 11% 折算）
EXPORT_REBATE_RATE = 0.11

# 默认清关服务费 (USD per shipment)
CUSTOMS_CLEARANCE_FEE_USD = 200

# 默认包装成本 (USD per ton)
PACKAGING_COST_USD_PER_TON = 18

# 利润阈值
PROFIT_HEALTHY = (0.15, 0.25)   # 15-25% 是健康区
PROFIT_WARNING_THRESHOLD = 0.10


# ================================================================
# Quote Engine
# ================================================================

def _estimate_ocean_freight_usd(target_country: str, *, container_type: str = "20GP",
                                 units: int = 1) -> float:
    """按地区返回海运基础运价（USD）。"""
    # 国家 → 区域启发式
    lc = target_country.lower()
    region = "southeast_asia"  # default fallback
    if lc in ("ae", "sa", "qa", "kw", "bh", "om", "iq", "ir", "ye"):
        region = "middle_east"
    elif lc in ("ng", "gh", "ci", "sn", "ml", "bj"):
        region = "west_africa"
    elif lc in ("ke", "tz", "et", "ug", "rw", "mz", "zm"):
        region = "east_africa"
    elif lc in ("pk", "in", "bd", "lk"):
        region = "south_asia"
    elif lc in ("us", "ca"):
        region = "north_america_west"
    elif lc in ("mx", "gt", "hn", "sv", "ni", "cr", "pa"):
        region = "north_america_east"
    elif lc in ("br", "ar", "uy", "cl", "co", "pe", "ve", "ec"):
        region = "south_america_east"
    elif lc in ("de", "fr", "it", "es", "nl", "pl", "gb", "pt"):
        region = "europe"
    elif lc in ("au", "nz"):
        region = "oceania"

    base = OCEAN_FREIGHT_USD_BY_REGION.get(region, 2000.0)
    return base * units


def _unit_price_in_usd(price: float, currency: str) -> float:
    """把任意币种单价换算 USD。"""
    rate = FX_RATES_USD.get(currency.upper())
    if rate is None:
        raise InvalidInput(f"unsupported currency: {currency!r}")
    if rate == 1.0:
        return float(price)
    # FX_RATES_USD 含义是 1 USD = X (currency)；price / rate = USD
    return float(price) / rate


def _format_money(amount_usd: float, currency: str = "USD") -> str:
    rate = FX_RATES_USD.get(currency.upper(), 1.0)
    if currency.upper() == "USD":
        return f"USD {amount_usd:,.2f}"
    converted = amount_usd * rate
    return f"{currency} {converted:,.2f} (USD {amount_usd:,.2f})"


def calculate_quote(
    *,
    sku: Dict[str, Any],
    quantity_tons: float,
    target_country: str,
    incoterm: str = "FOB",
    target_currency: str = "USD",
    profit_margin: float = 0.18,
    packaging_per_ton: float = PACKAGING_COST_USD_PER_TON,
    containers: int = 1,
) -> Dict[str, Any]:
    """生成 FOB/CIF/DDP 3 套报价。

    Returns dict with 'fob', 'cif', 'ddp' each containing subtotal breakdown.
    """
    if quantity_tons <= 0:
        raise InvalidInput(f"quantity_tons must be > 0, got {quantity_tons}")
    if profit_margin < 0 or profit_margin > 0.6:
        raise InvalidInput(f"profit_margin must be in [0, 0.6], got {profit_margin}")

    # 工厂基础价（转 USD）
    currency = sku.get("currency", "USD")
    unit_usd = _unit_price_in_usd(float(sku.get("unit_price_per_ton", 0)), currency)
    factory_cost = unit_usd * quantity_tons
    packaging_cost = packaging_per_ton * quantity_tons

    # 出口退税（FOB price 已扣除 — 视为工厂收入减少）
    # 简化：FOB 报价 = (factory_cost - rebate) * (1 + margin) + packaging
    rebate_savings = factory_cost * EXPORT_REBATE_RATE
    fob_subtotal = (factory_cost - rebate_savings) * (1 + profit_margin) + packaging_cost

    ocean = _estimate_ocean_freight_usd(target_country, units=containers)
    insurance = fob_subtotal * INSURANCE_RATE
    cif_subtotal = fob_subtotal + ocean + insurance

    # 目的港关税 stub：按发达 / 发展中估 6%
    target_duty_rate = 0.06
    customs_duty = cif_subtotal * target_duty_rate
    ddp_subtotal = cif_subtotal + customs_duty + CUSTOMS_CLEARANCE_FEE_USD

    # 利润健康检查 — 基于 FOB 角度
    profit_usd = fob_subtotal - factory_cost - packaging_cost + rebate_savings
    margin_realized = profit_usd / (fob_subtotal + 1e-9)
    if margin_realized < PROFIT_WARNING_THRESHOLD:
        profit_health = "LOW (< 10%)"
        profit_warning = (f"Realized margin {margin_realized:.1%} below 10% threshold. "
                            f"Consider raising unit price or reducing costs.")
    elif margin_realized < PROFIT_HEALTHY[0]:
        profit_health = "BELOW_HEALTHY (10-15%)"
        profit_warning = (f"Margin {margin_realized:.1%} below healthy floor (15%). "
                            f"Negotiate a higher price next round.")
    elif margin_realized > PROFIT_HEALTHY[1]:
        profit_health = "HIGH (> 25%)"
        profit_warning = (f"Margin {margin_realized:.1%} above healthy ceiling (25%). "
                            f"Verify this won't lose the deal.")
    else:
        profit_health = "HEALTHY (15-25%)"
        profit_warning = None

    payment_terms = _suggest_payment_terms(incoterm, target_country, margin_realized)

    result = {
        "$schema": "hlzd/quotation-gen/v1",
        "sku": sku.get("sku"),
        "quantity_tons": quantity_tons,
        "target_country": target_country,
        "currency": target_currency,
        "profit_margin_assumed": profit_margin,
        "components": {
            "factory_unit_price_usd": unit_usd,
            "factory_cost_usd": round(factory_cost, 2),
            "packaging_cost_usd": round(packaging_cost, 2),
            "export_rebate_usd": round(rebate_savings, 2),
            "ocean_freight_usd": round(ocean, 2),
            "insurance_usd": round(insurance, 2),
            "target_duty_rate": target_duty_rate,
            "target_duty_usd": round(customs_duty, 2),
            "customs_clearance_fee_usd": CUSTOMS_CLEARANCE_FEE_USD,
        },
        "incoterms": {
            "FOB": {
                "total_usd": round(fob_subtotal, 2),
                "unit_price_usd_per_ton": round(fob_subtotal / quantity_tons, 2),
            },
            "CIF": {
                "total_usd": round(cif_subtotal, 2),
                "unit_price_usd_per_ton": round(cif_subtotal / quantity_tons, 2),
            },
            "DDP": {
                "total_usd": round(ddp_subtotal, 2),
                "unit_price_usd_per_ton": round(ddp_subtotal / quantity_tons, 2),
            },
        },
        "profit_realized": {
            "absolute_usd": round(profit_usd, 2),
            "ratio": round(margin_realized, 4),
            "health": profit_health,
            "warning": profit_warning,
        },
        "payment_terms": payment_terms,
    }
    return result


def _suggest_payment_terms(incoterm: str, target_country: str,
                            margin_realized: float) -> Dict[str, Any]:
    """账期建议 — 综合考虑风险与利润。

    Default: 30% T/T advance + 70% T/T against B/L copy
    高风险国家 / 低利润 → LC at sight
    """
    high_risk_countries = {"iran", "north korea", "syria", "iraq"}
    is_high_risk = target_country.lower() in high_risk_countries

    if is_high_risk:
        return {
            "primary": "100% T/T in advance (pre-shipment)",
            "fallback": "Irrevocable L/C at sight from tier-1 bank (HSBC / JPM / Citi)",
            "risk_note": "High-risk destination: full advance or top-tier L/C only.",
        }
    if margin_realized < 0.10:
        return {
            "primary": "Irrevocable L/C at sight",
            "fallback": "30% T/T advance + 70% L/C at sight",
            "risk_note": "Thin margin: payment security takes priority over flexibility.",
        }
    return {
        "primary": "30% T/T advance + 70% T/T against B/L copy",
        "fallback": "Irrevocable L/C at sight",
        "risk_note": None,
    }


# ================================================================
# Pipeline
# ================================================================

def quote_for_solution(solution: Dict[str, Any], quantity_tons: float,
                        target_country: str, *,
                        incoterm: str = "FOB",
                        target_currency: str = "USD",
                        profit_margin: float = 0.18,
                        containers: int = 1) -> Dict[str, Any]:
    """对 solution-match 的单个 plan 出报价。

    solution_match 单 plan 形如：
      {"tier": "best_match", "sku": "...", "specs": { "unit_price_per_ton": ... }, ...}
    """
    sku_meta = {"sku": solution.get("sku"), "currency": "USD"}
    # 优先从 plan.specs 拿 unit_price_per_ton
    unit = solution.get("specs", {}).get("unit_price_per_ton")
    if unit is None:
        raise InvalidInput(f"solution {solution.get('sku')} missing unit_price_per_ton")
    sku_meta["unit_price_per_ton"] = unit

    return calculate_quote(
        sku=sku_meta,
        quantity_tons=quantity_tons,
        target_country=target_country,
        incoterm=incoterm,
        target_currency=target_currency,
        profit_margin=profit_margin,
        containers=containers,
    )
