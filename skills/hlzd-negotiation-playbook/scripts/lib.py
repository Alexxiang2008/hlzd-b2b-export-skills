"""hlzd-negotiation-playbook shared library.

让步路径推演引擎：
- 输入：原始报价 + 客户出价 + 红线（min_price / max_lead_time / min_payment_days）
- 输出：3 轮让步轨迹（round 1 / 2 / 3）+ 红线 hit 提示 + 决胜/暂停建议

设计：
- 价格让步：等比下降（让首次让步最大，后续递增线）
- 交期让步：少量递推
- 账期让步：30/70 → 20/80 → 0/100 三段
- 红线保护：每次让不让都 检查是否触碰 min/max
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


def get_logger(name: str = "hlzd-negotiation-playbook") -> logging.Logger:
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

class NegotiationError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-negotiation-playbook",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


class InvalidInput(NegotiationError):
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


# ================================================================
# Defaults
# ================================================================

# 价格让步幅度（相对初始报价百分比，建议 5 / 3 / 2 — 递减）
DEFAULT_PRICE_CONCESSION_PCT: List[float] = [0.05, 0.03, 0.02]
DEFAULT_LEAD_TIME_CONCESSION_DAYS: List[int] = [0, 5, 10]
DEFAULT_PAYMENT_TERM_PATH: List[Tuple[int, int]] = [
    (30, 70),  # 30% advance + 70% against B/L
    (20, 80),
    (10, 90),
]


# ================================================================
# 解析客户出价
# ================================================================

def parse_offer(text: str) -> Dict[str, Any]:
    """从客户自然语言出价中尝试抽数字。

    输入样例：
      "We can pay USD 1300 per ton" → target_price = 1300
      "Can you deliver in 60 days?" → desired_lead = 60
      "30% advance + 70% LC at sight" → payment = (30, 70, "lc")
    """
    out: Dict[str, Any] = {}

    # 价格
    price_m = re.search(r"(?:USD|EUR|\$|€)\s*([\d,]+(?:\.\d+)?)", text)
    if price_m:
        out["target_price"] = float(price_m.group(1).replace(",", ""))

    # 交期
    lead_m = re.search(r"(\d+)\s*(?:days?|working days?|d\b)", text, re.IGNORECASE)
    if lead_m:
        out["desired_lead_days"] = int(lead_m.group(1))

    # 账期
    pay_m = re.search(r"(\d+)\s*%\s*advance|advance\s+(\d+)\s*%", text, re.IGNORECASE)
    if pay_m:
        adv = int((pay_m.group(1) or pay_m.group(2) or "0"))
        out["advance_pct"] = adv
        out["balance_pct"] = 100 - adv

    lc_m = re.search(r"\b(LC|L/C|letter of credit)\b", text, re.IGNORECASE)
    if lc_m:
        out["payment_method_hint"] = "lc"

    return out


# ================================================================
# 让步推演
# ================================================================

def simulate_price(price_initial: float, target_price: float,
                    concessions_pct: List[float] = DEFAULT_PRICE_CONCESSION_PCT,
                    ) -> List[Dict[str, Any]]:
    """价格让步轨迹生成。

    每轮让步 = price_initial * (1 - sum(concessions_pct_so_far))
    红线：target_price 是客户出价，不能低于（让价不能亏本卖）
    """
    if price_initial <= 0:
        raise InvalidInput(f"price_initial must be > 0, got {price_initial}")
    if target_price <= 0:
        raise InvalidInput(f"target_price must be > 0, got {target_price}")

    rounds: List[Dict[str, Any]] = []
    cum_pct = 0.0
    current_price = price_initial
    for i, p in enumerate(concessions_pct, 1):
        cum_pct += p
        proposed_price = round(price_initial * (1 - cum_pct), 2)
        breaches_redline = proposed_price < target_price
        rounds.append({
            "round": i,
            "concession_pct": p,
            "cumulative_concession_pct": round(cum_pct, 4),
            "proposed_price_usd": proposed_price,
            "delta_from_initial_usd": round(proposed_price - price_initial, 2),
            "delta_from_target_usd": round(proposed_price - target_price, 2),
            "breaches_redline": breaches_redline,
        })
        current_price = proposed_price
        if breaches_redline:
            # 后面的 round 仍列出但标注无效
            continue

    return rounds


def simulate_lead_time(initial_lead: int, desired_lead: int,
                        concessions: List[int] = DEFAULT_LEAD_TIME_CONCESSION_DAYS,
                        ) -> List[Dict[str, Any]]:
    """交期让步轨迹。

    initial_lead: 工厂原始 lead time（天）
    desired_lead: 客户期望 lead time
    concessions: 每轮减少的天数（v0.1 默认：0 / 5 / 10）
    breaches_redline: 该轮让步后仍达不到 desired_lead（cost too high to satisfy customer）
    """
    if initial_lead <= 0:
        raise InvalidInput(f"initial_lead must be > 0, got {initial_lead}")
    if desired_lead <= 0:
        raise InvalidInput(f"desired_lead must be > 0, got {desired_lead}")

    rounds: List[Dict[str, Any]] = []
    cum = 0
    for i, c in enumerate(concessions, 1):
        cum += c
        new_lead = max(initial_lead - cum, desired_lead)
        # breach = 该 round 后 (initial_lead - cum) 仍大于 desired_lead
        breaches = (initial_lead - cum) > desired_lead
        rounds.append({
            "round": i,
            "concession_days": c,
            "new_lead_days": new_lead,
            "breaches_redline": breaches,
        })
    return rounds


def simulate_payment_terms(initial_advance_pct: int = 30,
                            path: List[Tuple[int, int]] = DEFAULT_PAYMENT_TERM_PATH,
                            ) -> List[Dict[str, Any]]:
    """账期让步轨迹。

    initial_advance_pct: 当前报价里 advance 占比
    path: 让步候选 (advance_pct, balance_pct)
    """
    rounds: List[Dict[str, Any]] = []
    for i, (adv, bal) in enumerate(path, 1):
        rounds.append({
            "round": i,
            "advance_pct": adv,
            "balance_pct": bal,
            "delta_from_initial_pct": adv - initial_advance_pct,
        })
    return rounds


# ================================================================
# 综合推演 + 决胜 / 暂停建议
# ================================================================

def recommend_action(
    price_rounds: List[Dict[str, Any]],
    lead_rounds: List[Dict[str, Any]],
    payment_rounds: List[Dict[str, Any]],
    *,
    lose_to_competitor_risk: bool = False,
) -> Dict[str, str]:
    """综合三轴决策 — 给建议：accept / counter / walk-away / defer。"""
    last_price = price_rounds[-1] if price_rounds else {}
    any_price_breach = any(r.get("breaches_redline") for r in price_rounds)
    any_lead_breach = any(r.get("breaches_redline") for r in lead_rounds)

    if any_price_breach and any_lead_breach:
        return {
            "decision": "walk_away",
            "rationale": "Both price and lead-time concessions breach redline. Recommend walking away or escalating to senior management for non-standard approval.",
            "next_step": "hlzd-negotiation-playbook (re-run with new target) OR manual review.",
        }
    if any_price_breach and not lose_to_competitor_risk:
        return {
            "decision": "counter",
            "rationale": "Price cannot reach customer target without margin loss. Counter with smaller scope (e.g. drop tier to economy)",
            "next_step": "hlzd-solution-match (re-tier the plan to economy)",
        }
    if any_lead_breach:
        return {
            "decision": "counter_with_freight",
            "rationale": "Lead-time cannot meet target. Offer partial air freight (buyer pays premium)",
            "next_step": "manual proposal with dual-incoterm (CIF + partial air)",
        }
    if lose_to_competitor_risk:
        return {
            "decision": "accept_round_3",
            "rationale": "Competitor threat is real; recommend accepting round 3 (final) offer to seal the deal",
            "next_step": "send final quote + escrow / LC setup",
        }
    return {
        "decision": "accept_round_2",
        "rationale": "Default path: two-round concession + lock. Round 3 reserved if renewal cycle.",
        "next_step": "send round 2 quote + set payment terms per payment_rounds[1]",
    }


# ================================================================
# Pipeline
# ================================================================

def run_playbook(
    *,
    initial_quote: Dict[str, Any],
    customer_response: Dict[str, Any],
    redlines: Optional[Dict[str, Any]] = None,
    concessions: Optional[Dict[str, List[float]]] = None,
    lose_to_competitor_risk: bool = False,
) -> Dict[str, Any]:
    """完整推演：
    - initial_quote（来自 hlzd-quotation-gen 输出）
    - customer_response（target_price / desired_lead / payment 等）
    - redlines {min_acceptable_price, max_lead_time_days, min_advance_pct}
    - concessions {price_pct: [0.05,0.03,0.02], lead_days: [0,5,10]}
    """
    redlines = redlines or {}
    cons = concessions or {}

    price_initial = float(initial_quote.get("incoterms", {}).get("FOB", {}).get(
        "total_usd", 0)) / max(1, initial_quote.get("quantity_tons", 1))  # per-ton
    target_price = float(customer_response.get("target_price") or
                          redlines.get("min_acceptable_price") or price_initial * 0.85)

    price_pct = cons.get("price_pct", DEFAULT_PRICE_CONCESSION_PCT)
    price_rounds = simulate_price(price_initial, target_price, price_pct)

    initial_lead = int(initial_quote.get("components", {}).get(
        "estimated_lead_days", 30))   # stub
    desired_lead = int(customer_response.get("desired_lead_days") or
                         redlines.get("max_lead_time_days") or initial_lead)
    lead_conc = cons.get("lead_days", DEFAULT_LEAD_TIME_CONCESSION_DAYS)
    lead_rounds = simulate_lead_time(initial_lead, desired_lead, lead_conc)

    initial_advance_pct = int(customer_response.get("advance_pct", 30))
    payment_rounds = simulate_payment_terms(initial_advance_pct)

    action = recommend_action(price_rounds, lead_rounds, payment_rounds,
                                lose_to_competitor_risk=lose_to_competitor_risk)

    return {
        "$schema": "hlzd/negotiation-playbook/v1",
        "initial_state": {
            "price_initial_usd_per_ton": price_initial,
            "lead_days_initial": initial_lead,
            "advance_pct_initial": initial_advance_pct,
            "target_price_usd_per_ton": target_price,
        },
        "redlines": {
            "price_floor_usd_per_ton": redlines.get("min_acceptable_price"),
            "max_lead_days": redlines.get("max_lead_time_days"),
            "min_advance_pct": redlines.get("min_advance_pct"),
        },
        "rounds": {
            "price": price_rounds,
            "lead_time": lead_rounds,
            "payment_terms": payment_rounds,
        },
        "red_line_breached": {
            "price": any(r.get("breaches_redline") for r in price_rounds),
            "lead_time": any(r.get("breaches_redline") for r in lead_rounds),
        },
        "decision": action,
    }
