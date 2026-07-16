"""EU Consolidated Sanctions List check.

v0.1 静态 csv.
v0.2 升级: 拉取 EU 实时 consolidated list (CFSP decisions).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lib  # noqa: E402

SOURCE_NAME = "eu_consolidated"
SOURCE_VERSION = "static_2026_q3"


def _load_rows() -> List[Dict[str, str]]:
    return lib.load_sanctions_csv("eu_consolidated.csv")


def _iter_names(row: Dict[str, str]) -> List[str]:
    names = [row.get("name", "").strip()]
    aliases = (row.get("alias_names", "") or "")
    for a in aliases.split("|"):
        if a.strip():
            names.append(a.strip())
    return [n for n in names if n]


def check_buyer(
    buyer_name: str,
    *,
    rows: Optional[List[Dict[str, str]]] = None,
) -> lib.CheckResult:
    if rows is None:
        rows = _load_rows()
    flags: List[lib.CheckFlag] = []
    norm_buyer = lib.normalize_name(buyer_name)
    matched = False
    metadata: Dict[str, Any] = {"rows_loaded": len(rows), "matches": []}

    for row in rows:
        candidates = _iter_names(row)
        for c in candidates:
            c_norm = lib.normalize_name(c)
            # 双向 fuzzy 匹配：normal 后任一含另一 + token 级共享
            tok_buyer = set(norm_buyer.split()) - lib.NAME_TOKEN_STOPWORDS
            tok_cand = set(c_norm.split()) - lib.NAME_TOKEN_STOPWORDS
            shared = tok_buyer & tok_cand
            # Long-token match: any token of length >= 6 (e.g. "Huawei",
            # "Wagner", "Hezbollah", "Tornado") shared AND c_norm len >= 6
            # (after removing stopwords to avoid "industrial" / "group" matches)
            long_shared = any(len(t) >= 6 for t in shared)
            token_match = len(shared) >= 1 and long_shared and len(c_norm) >= 6
            matched_fuzzy = (
                norm_buyer == c_norm
                or (c_norm and len(c_norm) >= 6 and c_norm in norm_buyer)
                or (norm_buyer and len(norm_buyer) >= 6 and norm_buyer in c_norm)
                or token_match
            )
            if matched_fuzzy:
                flags.append(lib.CheckFlag(
                    rule_id=f"EU-CONSOLIDATED-{row.get('program', 'UNK')}",
                    severity="BLOCK",
                    source=SOURCE_NAME,
                    evidence=row.get("name", ""),
                    rationale=f"Buyer listed under EU consolidated sanctions (program: {row.get('program', 'unknown')}).",
                    recommended_action="HALT + EU sanctions compliance review.",
                ))
                metadata["matches"].append({
                    "entity": row.get("name"),
                    "program": row.get("program"),
                    "matched_via": c,
                })
                matched = True
                break
        if matched:
            continue

    return lib.CheckResult(
        check_name="eu_consolidated_name_match",
        source_version=SOURCE_VERSION,
        matched=matched,
        flags=flags,
        metadata=metadata,
    )
