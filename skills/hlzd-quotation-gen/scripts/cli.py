#!/usr/bin/env python3
"""hlzd-quotation-gen CLI.

输入：
  1. SKU dict (内含 unit_price_per_ton / currency)
  2. 询盘 (quantity + 目的港 + 贸易术语)

用法：
  py scripts/cli.py --sku-son '{...}' --quantity 500 --country SA --incoterm FOB
  py scripts/cli.py --input sku.json --quantity 500 --country SA
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def _load_sku(args: argparse.Namespace) -> Dict[str, Any]:
    if args.sku_json:
        return json.loads(args.sku_json)
    if args.stdin:
        return json.loads(sys.stdin.read())
    if args.input:
        return json.loads(Path(args.input).read_text(encoding="utf-8"))
    raise lib.InvalidInput("must provide --sku-json or --stdin or --input")


def cli() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-quotation-gen")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--sku-json", help="JSON string of SKU dict")
    grp.add_argument("--stdin", "-s", action="store_true")
    grp.add_argument("--input", "-i", help="Path to SKU JSON")
    parser.add_argument("--quantity", "-q", type=float, required=True,
                         help="Quantity in tons")
    parser.add_argument("--country", "-c", required=True,
                         help="Target country ISO / shortcut code (ae / sa / us / ng ...)")
    parser.add_argument("--incoterm", default="FOB", choices=["FOB", "CIF", "DDP"])
    parser.add_argument("--currency", default="USD",
                         help="Quote target currency")
    parser.add_argument("--margin", type=float, default=0.18,
                         help="Profit margin (0.18 = 18%)")
    parser.add_argument("--containers", type=int, default=1, help="20GP containers")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--pretty", "-p", action="store_true")
    args = parser.parse_args()

    try:
        sku = _load_sku(args)
        quote = lib.calculate_quote(
            sku=sku,
            quantity_tons=args.quantity,
            target_country=args.country,
            incoterm=args.incoterm,
            target_currency=args.currency,
            profit_margin=args.margin,
            containers=args.containers,
        )
    except lib.QuotationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    out_str = json.dumps(quote, ensure_ascii=False, indent=indent)
    print(out_str)

    if args.output:
        Path(args.output).write_text(out_str, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(cli())
