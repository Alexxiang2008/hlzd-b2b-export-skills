#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""软条款扫描 — 从 references/catalogs/soft_clauses_catalog.md 读取模式命中"""
import re
import sys
from pathlib import Path

CATALOG_PATH = Path(__file__).parent.parent / "references" / "catalogs" / "soft_clauses_catalog.md"


def _load_patterns() -> list:
    """从 catalog 解析软条款 pattern（格式：`- **触发关键词**：...`）"""
    if not CATALOG_PATH.exists():
        return []
    text = CATALOG_PATH.read_text(encoding="utf-8")
    patterns = []
    current_id = None
    current_keywords = []
    current_risk = None
    for line in text.splitlines():
        m_id = re.match(r"^### (SC-[A-Z]+-\d+):", line)
        if m_id:
            if current_id and current_keywords:
                patterns.append(
                    {"id": current_id, "keywords": current_keywords, "risk": current_risk}
                )
            current_id = m_id.group(1)
            current_keywords = []
            current_risk = None
            continue
        m_kw = re.match(r"^- \*\*触发关键词\*\*：(.+)$", line)
        if m_kw and current_id:
            # 提取反引号包裹的关键词列表（支持斜杠分隔多个备选）
            current_keywords = re.findall(r"`([^`]+)`", m_kw.group(1))
            current_keywords = [k.strip().lower() for k in current_keywords if k.strip()]
            continue
        m_risk = re.match(r"^- \*\*风险\*\*：(.+)$", line)
        if m_risk and current_id:
            current_risk = m_risk.group(1).strip()
    if current_id and current_keywords:
        patterns.append({"id": current_id, "keywords": current_keywords, "risk": current_risk})
    return patterns


_PATTERNS = None


def _patterns():
    global _PATTERNS
    if _PATTERNS is None:
        _PATTERNS = _load_patterns()
    return _PATTERNS


def scan(text: str, lc_type: str = "COMMERCIAL_LC") -> list:
    """扫描软条款。返回命中的 [{id, risk, matched_keyword}] 列表"""
    t = text.lower()
    hits = []
    for pat in _patterns():
        # 按规则库过滤
        if lc_type == "COMMERCIAL_LC" and pat["id"].startswith(("SC-ISP", "SC-URDG")):
            continue
        if lc_type in ("STANDBY", "PERFORMANCE_STANDBY", "ADVANCE_PAYMENT_STANDBY", "BID_BOND_STANDBY", "DIRECT_PAY_STANDBY") and pat["id"].startswith(("SC-UCP", "SC-URDG")):
            continue
        if lc_type == "DEMAND_GUARANTEE" and pat["id"].startswith(("SC-UCP", "SC-ISP")):
            continue
        for kw in pat["keywords"]:
            if kw in t:
                hits.append({"id": pat["id"], "risk": pat["risk"], "matched": kw})
                break  # 一条只命中一次
    return hits


if __name__ == "__main__":
    sample = sys.argv[1] if len(sys.argv) > 1 else "approval of applicant required"
    print(scan(sample, "COMMERCIAL_LC"))