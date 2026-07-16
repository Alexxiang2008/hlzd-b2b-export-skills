"""hlzd-trade-compliance orchestrator.

编排 5 道检查 (4 buyer-side + 1 product dual-use), 然后综合成 1 个 ComplianceReport.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lib  # noqa: E402
from sources import (ofac_sdn, eu_consolidated, bis_entity,
                      country_embargo, dual_use)  # noqa: E402


def run_compliance_check(transaction: Dict[str, Any],
                          *,
                          product_description: str = "") -> lib.ComplianceReport:
    """Comprehensive compliance check.

    Input transaction keys (all required):
      - buyer_name: str
      - buyer_country: str (ISO / short name)

    Optional but recommended:
      - buyer_address / buyer_email
      - product, hs_code
      - end_use_country
      - incoterm
      - value_usd

    Returns ComplianceReport.
    """
    lib.validate_input(transaction)

    product = transaction.get("product", "industrial equipment")
    hs_code = transaction.get("hs_code", "")
    buyer_name = transaction.get("buyer_name", "")
    buyer_country = transaction.get("buyer_country", "")
    end_use_country = transaction.get("end_use_country", "")
    incoterm = transaction.get("incoterm", "")

    report = lib.ComplianceReport(
        product=product,
        hs_code=hs_code,
        buyer_name=buyer_name,
        buyer_country=buyer_country,
        end_use_country=end_use_country,
        incoterm=incoterm,
        timestamp_utc=lib.now_iso(),
    )

    # 5 道检查
    cr1 = ofac_sdn.check_buyer(buyer_name)
    cr2 = eu_consolidated.check_buyer(buyer_name)
    cr3 = bis_entity.check_buyer(buyer_name)
    cr4 = country_embargo.check_country(buyer_country, end_use_country=end_use_country)
    cr5 = dual_use.check_product(product, product_description, hs_code=hs_code)

    for cr in [cr1, cr2, cr3, cr4, cr5]:
        report.check_results.append(cr)
        report.audit_trail.append(lib.make_audit_entry(
            check=cr.check_name,
            version=cr.source_version,
            matched=cr.matched,
            flags_count=len(cr.flags),
        ))
        report.data_versions[cr.check_name] = cr.source_version
        report.data_source_attribution.append(
            f"{cr.check_name}:{cr.source_version}"
        )

    # 综合判定
    all_flags: List[lib.CheckFlag] = []
    for cr in report.check_results:
        all_flags.extend(cr.flags)

    if any(f.severity == "BLOCK" for f in all_flags):
        report.clearance = "BLOCKED"
        report.final_action = "DO NOT ship. Escalate to compliance officer for transaction freeze."
        report.rationale = "At least one BLOCK-level finding."
    elif any(f.severity == "REVIEW" for f in all_flags):
        report.clearance = "PENDING_REVIEW"
        report.final_action = "HOLD shipping until compliance officer signs off."
        report.rationale = "REVIEW-level findings require legal review before proceeding."
    else:
        report.clearance = "CLEARED"
        report.final_action = "Proceed with documentation; periodic re-check required."
        report.rationale = "No BLOCK or REVIEW findings across all 5 checks."

    return report
