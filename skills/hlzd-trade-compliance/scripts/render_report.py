"""hlzd-trade-compliance Markdown report renderer.

Convert ComplianceReport dict to a clean Markdown report suitable for sharing
with legal / compliance officer / customer.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


CLEARANCE_ICON = {
    "CLEARED": "[OK]",
    "PENDING_REVIEW": "[!]",
    "BLOCKED": "[X]",
}


SEVERITY_LABEL = {
    "BLOCK": "BLOCK",
    "REVIEW": "REVIEW",
    "INFO": "INFO",
}


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    clearance = report.get("clearance", "CLEARED")
    icon = CLEARANCE_ICON.get(clearance, "[?]")

    lines += [
        f"# {icon} Trade Compliance Report",
        "",
        f"- **Generated:** {report.get('timestamp_utc', 'N/A')}",
        f"- **Schema:** {report.get('$schema', report.get('schema_url', 'hlzd/trade-compliance/v1'))}",
        f"- **Clearance:** **{clearance}**",
        f"- **Final Action:** {report.get('final_action', '')}",
        f"- **Rationale:** {report.get('rationale', '')}",
        "",
        "## Transaction",
        "",
        f"- **Product:** {report.get('product', 'N/A')}",
        f"- **HS code:** {report.get('hs_code', 'N/A')}",
        f"- **Buyer:** {report.get('buyer_name', 'N/A')}",
        f"- **Buyer Country:** {report.get('buyer_country', 'N/A')}",
        f"- **End-Use Country:** {report.get('end_use_country', 'N/A') or '_unspecified_'}",
        f"- **Incoterm:** {report.get('incoterm', 'N/A') or '_unspecified_'}",
        "",
    ]

    # Check Results
    crs = report.get("check_results", []) or []
    lines += ["## Sanctions Screen Checks", ""]
    if not crs:
        lines.append("- _No checks run._")
    else:
        for cr in crs:
            lines.append(f"### {cr.get('check_name', '?')}")
            lines.append("")
            lines.append(f"- **Source Version:** `{cr.get('source_version', '?')}`")
            lines.append(f"- **Matched:** {'YES' if cr.get('matched') else 'no'}")
            meta = cr.get("metadata", {})
            if meta and "rows_loaded" in meta:
                lines.append(f"- **Rows loaded:** {meta['rows_loaded']}")
            lines.append("- **Flags raised:**")
            flags = cr.get("flags", []) or []
            if not flags:
                lines.append("  - _(none)_")
            else:
                for f in flags:
                    sev = f.get("severity", "?")
                    lines.append(f"  - **{sev}** - `{f.get('rule_id', '?')}` - evidence: _{f.get('evidence', '')}_")
                    lines.append(f"    - Rationale: {f.get('rationale', '')}")
                    lines.append(f"    - Action: {f.get('recommended_action', '')}")
            lines.append("")

    # Audit trail
    lines += ["## Audit Trail", ""]
    for entry in report.get("audit_trail", []):
        lines.append(
            f"- `{entry.get('timestamp_utc','?')}` **{entry.get('check','?')}** "
            f"matched={entry.get('matched')} flags={entry.get('flags_count')} "
            f"data_version={entry.get('data_version')}"
        )
    lines.append("")

    # Data source attribution
    lines += ["## Data Source Attribution", ""]
    versions = report.get("data_versions", {})
    if versions:
        for k, v in versions.items():
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines += [
        "---",
        "",
        "**Disclaimer.** This v0.1 tool uses static subsets of OFAC SDN, EU "
        "Consolidated, and BIS Entity lists. Production use requires real-time "
        "list updates via official APIs. Always escalate BLOCK/REVIEW findings "
        "to a qualified export compliance officer.",
        "",
    ]
    return "\n".join(lines)
