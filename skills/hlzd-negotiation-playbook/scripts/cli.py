#!/usr/bin/env python3
"""hlzd-negotiation-playbook CLI.

输入：initial_quote (hlzd-quotation-gen 输出) + customer_response
输出：3 轮让步轨迹 + 红线 hit + 决胜 / 暂停建议
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def _load_json(args: argparse.Namespace, flag_path: str = "--quote") -> Dict[str, Any]:
    path = getattr(args, flag_path.lstrip("--").replace("-", "_"))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cli() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-negotiation-playbook")
    parser.add_argument("--quote", required=True, help="Path to initial quote JSON")
    parser.add_argument("--response", required=True,
                         help="Path to customer response text or JSON dict")
    parser.add_argument("--redline-price", type=float,
                         help="Min acceptable USD per ton (price floor)")
    parser.add_argument("--redline-lead", type=int, help="Max lead time days")
    parser.add_argument("--redline-advance", type=int,
                         help="Min advance payment pct")
    parser.add_argument("--competitor-risk", action="store_true",
                         help="Flag if competitor risk is real")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--pretty", "-p", action="store_true")
    args = parser.parse_args()

    initial_quote = json.loads(Path(args.quote).read_text(encoding="utf-8"))
    customer_response_raw = Path(args.response).read_text(encoding="utf-8")
    try:
        customer_response = json.loads(customer_response_raw)
    except json.JSONDecodeError:
        # 自然语言文本：试用 parse_offer
        customer_response = lib.parse_offer(customer_response_raw)

    redlines = {}
    if args.redline_price is not None:
        redlines["min_acceptable_price"] = args.redline_price
    if args.redline_lead is not None:
        redlines["max_lead_time_days"] = args.redline_lead
    if args.redline_advance is not None:
        redlines["min_advance_pct"] = args.redline_advance

    try:
        report = lib.run_playbook(
            initial_quote=initial_quote,
            customer_response=customer_response,
            redlines=redlines or None,
            lose_to_competitor_risk=args.competitor_risk,
        )
    except lib.NegotiationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    out_str = json.dumps(report, ensure_ascii=False, indent=indent)
    print(out_str)
    if args.output:
        Path(args.output).write_text(out_str, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
