"""Country-based embargo check (OFAC + EU 综合).

检查交易对手国家 OR 终端使用国家是否在制裁名单中.
- 静态 dict (v0.1)
- v0.2 升级: 接 OFAC sanctions API per country
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lib  # noqa: E402

SOURCE_NAME = "country_embargo"
SOURCE_VERSION = "static_2026_q3"


def check_country(
    buyer_country: str,
    *,
    end_use_country: str = "",
) -> lib.CheckResult:
    """同时检查 buyer_country 和 end_use_country.

    - buyer_country = 主买家 / 收件方
    - end_use_country = 商品最终消费地（合同上 End Use Country）
    """
    flags: List[lib.CheckFlag] = []
    matched = False
    metadata: Dict[str, Any] = {"matches": []}

    for label, country in (("buyer_country", buyer_country),
                             ("end_use_country", end_use_country)):
        if not country:
            continue
        country_norm = lib.normalize_country(country)
        for sanctioned_name, info in lib.COUNTRY_EMBARGOES.items():
            if country_norm == sanctioned_name:
                severity = info["severity"]
                flags.append(lib.CheckFlag(
                    rule_id=f"COUNTRY-EMBARGO-{sanctioned_name.upper().replace(' ', '-')}",
                    severity=severity,
                    source=SOURCE_NAME,
                    evidence=f"{label}={country!r}",
                    rationale=f"{label.replace('_', ' ').title()} {country!r} is subject to {info['rules']}.",
                    recommended_action=(
                        "BLOCK - DO NOT ship; US/EU/UN sanctions apply regardless of buyer identity."
                        if severity == "BLOCK"
                        else "HOLD - selective sanctions apply; legal review required."
                    ),
                ))
                metadata["matches"].append({
                    "field": label,
                    "country": country,
                    "rules": info["rules"],
                    "severity": severity,
                })
                matched = True
                break

    return lib.CheckResult(
        check_name="country_embargo_match",
        source_version=SOURCE_VERSION,
        matched=matched,
        flags=flags,
        metadata=metadata,
    )
