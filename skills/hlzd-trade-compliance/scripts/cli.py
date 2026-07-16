#!/usr/bin/env python3
"""hlzd-trade-compliance CLI.

输入：transaction JSON
输出：compliance_report JSON（clearance + flags + audit trail）

用法:
  py scripts/cli.py --input transaction.json
  cat transaction.json | py scripts/cli.py --stdin
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402
import check as chk  # noqa: E402


def _load_input(args: argparse.Namespace) -> Dict[str, Any]:
    if args.stdin:
        raw = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise lib.InvalidInputFormat("transaction must be a dict")
    return data


def cli() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-trade-compliance")
    parser.add_argument("--input", "-i", help="Path to transaction JSON")
    parser.add_argument("--stdin", "-s", action="store_true")
    parser.add_argument("--description", help="Optional product description override")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--pretty", "-p", action="store_true")
    args = parser.parse_args()

    if not args.stdin and not args.input:
        print("error: --input or --stdin required", file=sys.stderr)
        return 2

    transaction = _load_input(args)
    product_description = args.description or transaction.get("product_description", "")

    try:
        report = chk.run_compliance_check(transaction, product_description=product_description)
    except lib.ComplianceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = lib.ComplianceReport.to_dict(report) if hasattr(report, "to_dict") else report.__dict__
    out_dict = _serialize_report(out)
    indent = 2 if args.pretty else None
    out_str = json.dumps(out_dict, ensure_ascii=False, indent=indent)
    print(out_str)

    if args.output:
        Path(args.output).write_text(out_str, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)

    # exit code: 0 if cleared, 1 if review, 2 if blocked
    return {"CLEARED": 0, "PENDING_REVIEW": 1, "BLOCKED": 2}.get(report.clearance, 1)


def _serialize_report(report: Any) -> Dict[str, Any]:
    """Convert dataclass-based report to nested dict."""
    if isinstance(report, dict):
        return report
    if hasattr(report, "to_dict"):
        return report.to_dict()
    return dict(report)


if __name__ == "__main__":
    sys.exit(cli())
