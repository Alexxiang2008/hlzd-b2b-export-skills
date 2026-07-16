"""ECC / 双用途商品粗筛 check.

v0.1: keyword-based 启发式.
v0.2: 接 BIS Commerce Control List API.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lib  # noqa: E402

SOURCE_NAME = "eccn_dual_use"
SOURCE_VERSION = "static_2026_q3"


def check_product(
    product_name: str,
    product_description: str = "",
    *,
    hs_code: str = "",
) -> lib.CheckResult:
    """检查产品名 + 描述 + HS code 是否命中 ECCN 双用途关键词."""
    text_blobs = [product_name, product_description, hs_code]
    combined = " ".join(t for t in text_blobs if t).lower()
    flags: List[lib.CheckFlag] = []
    matched = False
    metadata: Dict[str, Any] = {"matches": []}

    # 1) 关键词粗筛
    for kw in lib.DUAL_USE_KEYWORDS:
        if kw.lower() in combined:
            flags.append(lib.CheckFlag(
                rule_id="DUAL-USE-KEYWORD",
                severity="REVIEW",
                source=SOURCE_NAME,
                evidence=kw,
                rationale=f"Product description / HS code references dual-use keyword '{kw}'.",
                recommended_action="HOLD + confirm ECCN classification; export license may be required.",
            ))
            metadata["matches"].append({"keyword": kw, "kind": "keyword"})
            matched = True

    # 2) HS 编码 → ECCN 映射（v0.1 简化 — 静态 map）
    eccn_map = {
        "8541": {"eccn": "3A001", "rationale": "Semiconductor devices may be ECCN 3A001"},
        "8471": {"eccn": "4A003", "rationale": "Computers may be ECCN 4A003"},
        "9018": {"eccn": "5A002", "rationale": "Medical or laser; verify ECCN"},
        "8802": {"eccn": "9A012", "rationale": "Aircraft / UAV; verify ECCN"},
    }
    hs_prefix = (hs_code or "").strip()[:4]
    if hs_prefix in eccn_map:
        info = eccn_map[hs_prefix]
        flags.append(lib.CheckFlag(
            rule_id=f"ECCN-HS-{hs_prefix}",
            severity="REVIEW",
            source=SOURCE_NAME,
            evidence=f"HS {hs_prefix}",
            rationale=info["rationale"],
            recommended_action="HOLD + verify ECCN classification before quoting.",
        ))
        metadata["matches"].append({"hs_code": hs_prefix, **info})
        matched = True

    return lib.CheckResult(
        check_name="eccn_dual_use_keyword",
        source_version=SOURCE_VERSION,
        matched=matched,
        flags=flags,
        metadata=metadata,
    )
