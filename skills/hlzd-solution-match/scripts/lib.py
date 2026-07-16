"""hlzd-solution-match shared library.

输入：客户询盘（enquiry dict）+ 产品目录（SKU list）
输出：3 套方案（best_match / alternative / cost_effective）+ 风险检查

核心：5 维匹配评分 + 3 套方案生成 + 风险检查清单
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-solution-match") -> logging.Logger:
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

class SolutionMatchError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-solution-match",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


class InvalidInput(SolutionMatchError):
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


# ================================================================
# 内置产品目录（v0.1 静态 — 真实部署接 ERP）
# ================================================================

DEFAULT_CATALOG: List[Dict[str, Any]] = [
    {
        "sku": "OCTG-L80-95-BTC-PREMIUM",
        "category": "OCTG",
        "grade": "L80", "od_inch": 9.625, "connection": "BTC",
        "certifications": ["API 5CT", "ISO 11960", "NACE MR0175"],
        "applications": ["sour service", "oilfield", "downhole"],
        "capacity_per_month_tons": 800,
        "moq_tons": 30,
        "lead_time_days": 30,
        "currency": "USD",
        "unit_price_per_ton": 1480,    # 报价基准
        "tier": "premium",
        "tier_index": 3,               # 0=经济 1=标准 2=加强 3=高级
    },
    {
        "sku": "OCTG-N80-95-BTC-STANDARD",
        "category": "OCTG",
        "grade": "N80", "od_inch": 9.625, "connection": "BTC",
        "certifications": ["API 5CT", "ISO 11960"],
        "applications": ["oilfield", "downhole", "sweet service"],
        "capacity_per_month_tons": 1200,
        "moq_tons": 20,
        "lead_time_days": 25,
        "currency": "USD",
        "unit_price_per_ton": 1320,
        "tier": "standard",
        "tier_index": 1,
    },
    {
        "sku": "OCTG-J55-95-EUE-ECONOMY",
        "category": "OCTG",
        "grade": "J55", "od_inch": 9.625, "connection": "EUE",
        "certifications": ["API 5CT"],
        "applications": ["onshore", "shallow well", "sweet service"],
        "capacity_per_month_tons": 1500,
        "moq_tons": 20,
        "lead_time_days": 20,
        "currency": "USD",
        "unit_price_per_ton": 1080,
        "tier": "economy",
        "tier_index": 0,
    },
    {
        "sku": "PV-MODULE-450W-MONO",
        "category": "Solar Panel",
        "grade": "Mono", "watt": 450,
        "certifications": ["IEC 61215", "IEC 61730", "UL 1703"],
        "applications": ["rooftop", "commercial", "utility scale"],
        "capacity_per_month_watts": 5000000,
        "moq_watts": 50000,
        "lead_time_days": 21,
        "currency": "USD",
        "unit_price_per_watt": 0.18,
        "tier": "standard",
        "tier_index": 1,
    },
    {
        "sku": "STRUC-IPE-200-EN1090",
        "category": "Steel Structure",
        "shape": "IPE 200", "standard": "EN 1090",
        "certifications": ["EN 1090", "ISO 9001", "CE"],
        "applications": ["commercial building", "warehouse", "stadium"],
        "capacity_per_month_tons": 2000,
        "moq_tons": 50,
        "lead_time_days": 35,
        "currency": "USD",
        "unit_price_per_ton": 920,
        "tier": "standard",
        "tier_index": 1,
    },
]


# ================================================================
# Matching 评分
# ================================================================

def _norm(s: Any) -> str:
    """Stringify + lowercase + strip."""
    if s is None:
        return ""
    return str(s).strip().lower()


def _has_overlap(enquiry_terms: List[str], sku_terms: List[str]) -> Tuple[bool, List[str]]:
    """两边都小写，返回 overlap + matches。"""
    e = {_norm(t) for t in enquiry_terms if t}
    s = {_norm(t) for t in sku_terms if t}
    matches = sorted(e & s)
    return len(matches) > 0, matches


def _listify_application(text: str) -> List[str]:
    """把 inquiry 应用描述拆分关键词 → 应用 tag list。"""
    text = _norm(text)
    tags = []
    # 单个 token + 常见 multi-word
    candidates = [
        "sour service", "sweet service", "h2s",
        "oilfield", "downhole", "onshore", "offshore",
        "rooftop", "utility scale", "commercial",
        "warehouse", "stadium", "shallow well",
        "refinery", "petrochemical",
        "mining", "camp",
    ]
    for c in candidates:
        if c in text:
            tags.append(c)
    return tags


def _extract_certifications(text: str) -> List[str]:
    text = _norm(text)
    certs = []
    # 用 word-boundary-aware 检测：每个 cert 的两侧视为 token 边界
    candidates = [
        "api 5ct", "api 5l", "iso 11960", "iso 9001", "iso 14001",
        "nace mr0175", "en 1090",
        "iec 61215", "iec 61730", "ul 1703",
        "astm a53", "astm a106",
    ]
    for c in candidates:
        if re.search(rf"(?<![a-z]){re.escape(c)}(?![a-z])", text):
            certs.append(c)
    # 单 token 证书：要求前面是空白或首字符
    for token in ("ce", "rohs", "reach"):
        if re.search(rf"(?<![\w\-]){re.escape(token)}(?![\w\-])", text):
            if token not in certs:
                certs.append(token)
    return certs


def score_sku(enquiry: Dict[str, Any], sku: Dict[str, Any]) -> Dict[str, Any]:
    """5 维匹配评分：D1 规格 (30) / D2 数量 (15) / D3 交期 (20) / D4 价格 (15) / D5 风险 (20)"""
    missing: List[str] = []
    risks: List[str] = []

    # ---- D1 规格匹配 (30) ----
    d1 = 0
    d1_missing = []

    # 1.a 品类匹配
    enquiry_cat = _norm(enquiry.get("product_category", "") or enquiry.get("product", ""))
    sku_cat = _norm(sku.get("category", ""))
    if enquiry_cat and sku_cat:
        if enquiry_cat in sku_cat or sku_cat in enquiry_cat:
            d1 += 8
        else:
            d1_missing.append(f"category_mismatch(enq={enquiry_cat},sku={sku_cat})")

    # 1.b 认证匹配 — 询盘要的 cert，SKU 是否都覆盖？
    cert_text_bits = [enquiry.get("text", "") or ""]
    cert_text_bits.extend(enquiry.get("certifications_required") or [])
    enq_certs = _extract_certifications(" ".join(cert_text_bits))
    sku_certs = {_norm(c) for c in sku.get("certifications", [])}
    sku_certs = {_norm(c) for c in sku.get("certifications", [])}
    if enq_certs:
        missing_certs = [c for c in enq_certs if c not in sku_certs]
        if missing_certs:
            d1_missing.extend([f"cert_missing:{c}" for c in missing_certs])
            risks.extend([f"missing_cert:{c}" for c in missing_certs])
        else:
            d1 += 12  # 认证全命中
    elif sku_certs:
        d1 += 6   # SKU 有认证但询盘未提

    # 1.c 应用场景匹配
    enq_apps = _listify_application(
        " ".join([enquiry.get("text", ""), enquiry.get("application", "") or ""])
    )
    sku_apps = {_norm(a) for a in sku.get("applications", [])}
    if enq_apps:
        if any(a in sku_apps for a in enq_apps):
            d1 += 10
        else:
            d1_missing.append("application_mismatch")
    else:
        d1 += 5  # 询盘未指定应用 — 不扣分但也不全给

    d1 = min(d1, 30)

    # ---- D2 数量匹配 (15) ----
    d2 = 0
    d2_missing = []

    # 估量（quantity 字段）
    qty_str = enquiry.get("quantity", "") or ""
    qty_match = re.search(r"\d[\d,\.]*", str(qty_str))
    qty = float(qty_match.group(0).replace(",", "")) if qty_match else 0.0

    # SKU 月产能 / MOQ — 简化：只检查 SKU 内的 MOQ 字段
    sku_moq = float(sku.get("moq_tons", sku.get("moq_watts", 0)) or 0)
    sku_capacity = float(sku.get("capacity_per_month_tons",
                                 sku.get("capacity_per_month_watts", 0)) or 0)
    if qty > 0:
        if qty >= sku_moq:
            d2 += 8
        else:
            d2_missing.append(f"qty_below_moq(enq={qty},sku_moq={sku_moq})")
            risks.append("below_moq")
        if qty <= sku_capacity:
            d2 += 7
        else:
            d2_missing.append(f"qty_above_monthly_capacity(qty={qty},capacity={sku_capacity})")
            risks.append("capacity_stretch")
    else:
        d2 += 7   # 询盘未提数量 — 评分中性
        d2_missing.append("quantity_not_specified")
    d2 = min(d2, 15)

    # ---- D3 交期匹配 (20) ----
    d3 = 0
    d3_missing = []
    enq_lead_days = enquiry.get("lead_time_days")
    sku_lead = float(sku.get("lead_time_days", 0) or 0)
    if enq_lead_days is not None and sku_lead > 0:
        try:
            enq_lead = float(enq_lead_days)
            if enq_lead >= sku_lead:
                d3 += 20  # 产能覆盖客户期望
            elif enq_lead >= sku_lead * 0.7:
                d3 += 10  # 略微超期但可行
            else:
                d3_missing.append(f"lead_time_too_short(enq={enq_lead},sku={sku_lead})")
                risks.append("lead_time_risk")
        except (TypeError, ValueError):
            d3 += 10
            d3_missing.append("lead_time_unparseable")
    elif sku_lead > 0:
        d3 += 12   # 询盘未提交期 — 给中间分
        d3_missing.append("lead_time_not_specified")
    d3 = min(d3, 20)

    # ---- D4 价格梯度 (15) ----
    # tier_index=1 (standard) 拿满分；相邻 tier 拿 10；远距 tier 拿 0
    tier_index = int(sku.get("tier_index", 1) or 1)
    if tier_index == 1:
        d4 = 15
    elif tier_index in (0, 2):
        d4 = 10
    else:
        # tier 距离 standard 越远 → 越极端 → 0
        d4 = max(0, 15 - (abs(tier_index - 1) * 8))
    d4 = min(d4, 15)

    # ---- D5 风险检查 (20) ----
    d5 = 20
    if risks:
        # 每个风险扣 4 分，最低 0
        d5 = max(0, 20 - len(risks) * 4)
    d5_missing = [] if not risks else [f"risk:{r}" for r in risks[:5]]

    total = d1 + d2 + d3 + d4 + d5
    return {
        "sku": sku.get("sku", "?"),
        "D1_spec": {"score": d1, "max": 30, "missing": d1_missing},
        "D2_qty": {"score": d2, "max": 15, "missing": d2_missing},
        "D3_lead": {"score": d3, "max": 20, "missing": d3_missing},
        "D4_price_tier": {"score": d4, "max": 15, "missing": []},
        "D5_risk": {"score": d5, "max": 20, "missing": d5_missing},
        "total": total,
        "risks": risks,
    }


# ================================================================
# 3 套方案生成
# ================================================================

def recommend_three(enquiry: Dict[str, Any],
                     catalog: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """对 catalog 中所有 SKU 评分，挑 3 套。

    策略：
    1. 取评分前 5 的 SKU 集合
    2. best_match = 评分最高、且风险最少的
    3. alternative = 评分第二高、且风险不同（不同 tier）
    4. cost_effective = tier_index 最小（最低价）
    """
    cat = catalog if catalog is not None else DEFAULT_CATALOG
    if not cat:
        raise InvalidInput("catalog is empty")

    scored = []
    for sku in cat:
        try:
            s = score_sku(enquiry, sku)
        except Exception as exc:  # noqa: BLE001
            continue
        scored.append({**s, "sku_obj": sku})

    if not scored:
        raise InvalidInput("no SKU could be scored")

    # 排序：风险最少优先，再按 score 降序
    scored.sort(key=lambda r: (len(r["risks"]), -r["total"]))

    # best_match：评分最高
    best_match = scored[0]

    # alternative：与 best_match 不同 tier 的次高
    best_tier = best_match["sku_obj"].get("tier", "")
    alt_pool = [s for s in scored[1:] if s["sku_obj"].get("tier") != best_tier]
    alternative = alt_pool[0] if alt_pool else (scored[1] if len(scored) > 1 else best_match)

    # cost_effective：评分前 3 中 tier_index 最小
    top3 = scored[:3]
    cost_effective = min(top3, key=lambda r: r["sku_obj"].get("tier_index", 5))

    # safety：如果 best / alternative / cost 都同一 SKU（catalog 只有 1 条），允许重复
    return {
        "$schema": "hlzd/solution-match/v1",
        "enquiry_product": enquiry.get("product_category") or enquiry.get("product") or "",
        "evaluated_skus": len(scored),
        "best_match": _format_proposal(best_match, "best_match", "Recommended based on highest match score with lowest risk."),
        "alternative": _format_proposal(alternative, "alternative", "Backup option with different tier / risk profile."),
        "cost_effective": _format_proposal(cost_effective, "cost_effective", "Lowest priced viable option."),
        "all_risks": sorted({r for s in scored for r in s["risks"]}),
    }


def _format_proposal(scored: Dict[str, Any], tier_label: str,
                       rationale: str) -> Dict[str, Any]:
    sku = scored["sku_obj"]
    return {
        "tier": tier_label,
        "sku": sku.get("sku"),
        "category": sku.get("category"),
        "specs": {k: v for k, v in sku.items()
                  if k not in ("sku", "category") and isinstance(v, (str, int, float))},
        "match_score": scored["total"],
        "scoring_breakdown": {
            "D1_spec": scored["D1_spec"],
            "D2_qty": scored["D2_qty"],
            "D3_lead": scored["D3_lead"],
            "D4_price_tier": scored["D4_price_tier"],
            "D5_risk": scored["D5_risk"],
        },
        "risks": scored["risks"],
        "rationale": rationale,
    }
