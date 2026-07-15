#!/usr/bin/env python3
"""hlzd-customer-due-diligence CLI.

输入：buyer 列表 JSON (来自 hlzd-buyer-finder 输出 importers 字段)
输出：每 buyer 评分 + 合规粗筛 + routing recommendation

用法:
  py scripts/cli.py --input buyers.json
  py scripts/cli.py --input buyers.json --output diligence.json
  py scripts/cli.py --stdin < buyers.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def _load_input(args: argparse.Namespace) -> List[Dict[str, Any]]:
    if args.stdin:
        raw = sys.stdin.read()
        data = json.loads(raw)
    else:
        raw = Path(args.input).read_text(encoding="utf-8")
        data = json.loads(raw)

    # 兼容多种输入：
    # - 直接 list
    # - { "importers": [...] }
    # - { "importers": [...], ... } (buyer-finder 输出来源)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("importers", "buyers", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    raise lib.InvalidBuyerRecord("input must be list, or dict with 'importers' / 'buyers' key")


def cli() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-customer-due-diligence")
    parser.add_argument("--input", "-i", help="Path to buyers JSON file")
    parser.add_argument("--stdin", "-s", action="store_true")
    parser.add_argument("--output", "-o", help="Path to write diligence JSON")
    parser.add_argument("--pretty", "-p", action="store_true")
    args = parser.parse_args()

    if not args.stdin and not args.input:
        print("error: --input or --stdin required", file=sys.stderr)
        return 2

    buyers = _load_input(args)
    report = lib.evaluate_many(buyers)

    indent = 2 if args.pretty else None
    out_str = json.dumps(report, ensure_ascii=False, indent=indent)
    print(out_str)

    if args.output:
        Path(args.output).write_text(out_str, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)

    # Exit code: 0 = all green; 1 = some halt recommended (compliance/fraud)
    return 1 if report.get("halt_recommended", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(cli())
