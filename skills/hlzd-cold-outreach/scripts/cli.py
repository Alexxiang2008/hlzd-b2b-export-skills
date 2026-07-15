#!/usr/bin/env python3
"""hlzd-cold-outreach CLI.

输入：diligence.json（来自 hlzd-customer-due-diligence 输出）+ 产品 context
输出：每 buyer 一封邮件草稿 + Day 7/14 跟进序列

用法:
  py scripts/cli.py --input diligence.json --product "OCTG casing" \
                    --sender-company HLZD --sender-name "Alex"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def _load_input(args: argparse.Namespace) -> Dict[str, Any]:
    if args.stdin:
        raw = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")

    data = json.loads(raw)
    # 兼容多种输入：
    # { results: [...], ...}（来自 diligence）
    if isinstance(data, dict):
        for key in ("results", "buyers", "importers"):
            if isinstance(data.get(key), list):
                return {"results": data[key]}
    if isinstance(data, list):
        return {"results": data}
    return {"results": [data]}


def cli() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-cold-outreach")
    parser.add_argument("--input", "-i", help="Path to diligence JSON (or list)")
    parser.add_argument("--stdin", "-s", action="store_true")
    parser.add_argument("--product", "-p", default="industrial equipment",
                         help="Product name/category (used in template)")
    parser.add_argument("--sender-company", default="HLZD")
    parser.add_argument("--sender-name", default="Sales Team")
    parser.add_argument("--sender-email", default="sales@hlzd.example.com")
    parser.add_argument("--sender-phone", default="+86 138 0000 0000")
    parser.add_argument("--default-language", default="en", choices=["en", "es"])
    parser.add_argument("--default-customer-type", default="Manufacturer",
                         choices=list(lib.SUPPORTED_CUSTOMER_TYPES))
    parser.add_argument("--no-followups", action="store_true",
                         help="Don't generate Day 7/14 follow-up sequence")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    if not args.stdin and not args.input:
        print("error: --input or --stdin required", file=sys.stderr)
        return 2

    buyers = _load_input(args).get("results", [])

    product_context = {
        "product": args.product,
        "product_category": args.product,
        "sender_company": args.sender_company,
        "sender_name": args.sender_name,
        "sender_email": args.sender_email,
        "sender_phone": args.sender_phone,
    }

    report = lib.generate_for_buyers(
        buyers,
        product_context,
        default_customer_type=args.default_customer_type,
        default_language=args.default_language,
        include_followups=not args.no_followups,
    )

    indent = 2 if args.pretty else None
    out_str = json.dumps(report, ensure_ascii=False, indent=indent)
    print(out_str)

    if args.output:
        Path(args.output).write_text(out_str, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)

    return 0 if report.get("generated") else 1


if __name__ == "__main__":
    sys.exit(cli())
