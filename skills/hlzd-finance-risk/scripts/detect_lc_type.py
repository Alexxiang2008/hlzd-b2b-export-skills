#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L/C 类型检测 — 纯函数，无依赖"""

# 优先级 1: URDG 758 关键词
URDG_KEYWORDS = ("URDG 758", "DEMAND GUARANTEE", "COUNTER-GUARANTEE", "COUNTER GUARANTEE")

# 优先级 2: ISP98 关键词
STANDBY_BASE = ("STANDBY", "ISP98")
STANDBY_TYPES = [
    ("PERFORMANCE STANDBY", "PERFORMANCE_STANDBY"),
    ("ADVANCE PAYMENT", "ADVANCE_PAYMENT_STANDBY"),
    ("BID BOND", "BID_BOND_STANDBY"),
    ("TENDER BOND", "BID_BOND_STANDBY"),
    ("DIRECT PAY", "DIRECT_PAY_STANDBY"),
    ("INSURANCE STANDBY", "INSURANCE_STANDBY"),
]

# 优先级 3: UCP 600 关键词
UCP_KEYWORDS = ("UCP 600", "UCP600", "DOCUMENTARY CREDIT", "COMMERCIAL CREDIT")


def detect_lc_type(text: str) -> str:
    """识别 L/C 类型。返回值：DEMAND_GUARANTEE / *STANDBY / COMMERCIAL_LC / UNKNOWN"""
    t = text.upper()

    # 优先级 1: URDG 758
    for kw in URDG_KEYWORDS:
        if kw in t:
            return "DEMAND_GUARANTEE"

    # 优先级 2: ISP98（先细分，再归类）
    for kw in STANDBY_BASE:
        if kw in t:
            for sub_kw, lc_type in STANDBY_TYPES:
                if sub_kw in t:
                    return lc_type
            return "STANDBY"

    # 优先级 3: UCP 600 / 默认
    for kw in UCP_KEYWORDS:
        if kw in t:
            return "COMMERCIAL_LC"

    return "UNKNOWN"


if __name__ == "__main__":
    import sys
    sample = sys.argv[1] if len(sys.argv) > 1 else "DOCUMENTARY CREDIT UCP 600"
    print(detect_lc_type(sample))