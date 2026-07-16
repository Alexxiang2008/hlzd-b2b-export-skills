#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HLZD 角色检测 — 受益人 / 申请人 / 担保人"""

ROLE_KEYWORDS = (
    "APPLICANT",
    "BENEFICIARY",
    "GUARANTOR",
    "INSTRUCTING PARTY",
    "COUNTER-GUARANTOR",
)
WINDOW_CHARS = 300  # 角色字段后看 300 字符


def detect_role(text: str, hlzd_name: str = "HLZD") -> str:
    """根据 L/C 文本和 HLZD 公司名出现的位置判断角色。

    返回值：APPLICANT / BENEFICIARY / GUARANTOR / UNKNOWN
    """
    if not hlzd_name:
        return "UNKNOWN"
    upper = text.upper()
    hlzd_upper = hlzd_name.upper()

    for role in ROLE_KEYWORDS:
        idx = upper.find(role)
        if idx < 0:
            continue
        window = upper[idx: idx + WINDOW_CHARS]
        if hlzd_upper in window:
            return role.replace(" INSTRUCTING PARTY", "").replace("COUNTER-", "")
    return "UNKNOWN"


if __name__ == "__main__":
    import sys
    sample = sys.argv[1] if len(sys.argv) > 1 else "APPLICANT: HLZD CO LTD"
    name = sys.argv[2] if len(sys.argv) > 2 else "HLZD"
    print(detect_role(sample, name))