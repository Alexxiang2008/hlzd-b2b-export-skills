#!/usr/bin/env python3
"""hlzd-solution-match CLI.

输入：询盘（enquiry dict, JSON）+ 可选产品目录（catalog JSON）
输出：3 套方案 + 全部 SKU 评分 + 风险汇总

用法:
  py scripts/cli.py --input enquiry.json
  py scripts/cli.py --input enquiry.json --catalog catalog.json --pretty
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def _load_enquiry(args: argparse.Namespace) -> Dict[str, Any]:
    if args.stdin:
        raw = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, dict):
        return data
    raise lib.InvalidInput("enquiry must be dict")


def _load_catalog(args: argparse.Namespace, default: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not args.catalog:
        return default
    raw = Path(args.catalog).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise lib.InvalidInput("catalog must be list")
    return data


def cli() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-solution-match")
    parser.add_argument("--input", "-i", help="Path to enquiry JSON")
    parser.add_argument("--stdin", "-s", action="store_true")
    parser.add_argument("--catalog", help="Optional custom catalog JSON")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--pretty", "-p", action="store_true")
    args = parser.parse_args()

    if not args.stdin and not args.input:
        print("error: --input or --stdin required", file=sys.stderr)
        return 2

    enquiry = _load_enquiry(args)
    catalog = _load_catalog(args, lib.DEFAULT_CATALOG)
    try:
        report = lib.recommend_three(enquiry, catalog)
    except lib.SolutionMatchError as exc:
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
