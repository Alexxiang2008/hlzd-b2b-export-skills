#!/usr/bin/env python3
"""hlzd-buyer-finder CLI.

单入口：3 链路共用，按 --method 切换。

用法:
  # 链路 A (默认): 阿里发现竞对 → Volza 找买家
  py scripts/cli.py --product "CNC machining" --country US --method auto

  # 链路 B: 用户给竞对 → Volza 直接搜
  py scripts/cli.py --competitor "Xiamen Hym Metal Products Co., Ltd."
                  --competitor "Shenzhen Kaier Wo Prototyping Technology Co., Ltd."
                  --country US

  # 链路 C: 关键词 + 国家直接搜
  py scripts/cli.py --product "container house mining" --country US --method keyword

  # 输出 JSON 到文件 + 命令行 stdout
  py scripts/cli.py --product "..." --country US --output-json buyers.json --pretty

数据源：
- Alibaba 国际站搜索（自动发现中国供应商）
- Volza 海关数据（搜供应商 → 找买家）
- ImportGenius / 52WMB（占位）
- 公开进口商目录（兜底）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

# 让 sibling 模块可被 import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline  # noqa: E402
import lib  # noqa: E402


def _parse_csv(value: str) -> List[str]:
    if not value:
        return []
    out = []
    for token in value.replace("\n", ",").split(","):
        token = token.strip()
        if token:
            out.append(token)
    return out


def cli() -> int:
    parser = argparse.ArgumentParser(
        prog="hlzd-buyer-finder",
        description="3-link buyer finding pipeline (Alibaba + Volza + public directory)",
    )
    parser.add_argument("--product", "-p", help="Product keyword (e.g. 'CNC machining parts')")
    parser.add_argument("--country", "-c", help="Target country ISO code (e.g. US, AE, SA, BR)")
    parser.add_argument(
        "--method", "-m", default="auto", choices=["auto", "competitor", "keyword"],
        help="Pipeline method: auto (default) / competitor / keyword",
    )
    parser.add_argument(
        "--competitor", "-k", action="append", default=[],
        help="Supplier name (repeatable, used with --method=competitor). Comma-separated also ok.",
    )
    parser.add_argument("--max-competitors", type=int, default=5, help="Max competitors to discover (default 5)")
    parser.add_argument("--max-buyers", type=int, default=8, help="Max buyers per competitor (default 8)")
    parser.add_argument("--output-json", "-o", help="Output JSON file path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    args = parser.parse_args()

    # 参数级 sanity 检查
    if args.method == "competitor" and not args.competitor:
        print("error: --method=competitor requires --competitor (repeatable)", file=sys.stderr)
        return 2
    if args.method == "keyword" and not args.country:
        print("error: --method=keyword requires --country", file=sys.stderr)
        return 2
    if args.method in ("auto", "keyword") and not args.product:
        print(f"error: --method={args.method} requires --product", file=sys.stderr)
        return 2

    # 把 '--competitor "X, Y"' 拆分为多条
    competitors: List[str] = []
    for c in args.competitor:
        competitors.extend(_parse_csv(c))

    try:
        report = pipeline.run_pipeline(
            product=args.product or "",
            method=args.method,
            country_iso=args.country,
            competitors=competitors or None,
            max_competitors=args.max_competitors,
            max_buyers_per_competitor=args.max_buyers,
        )
    except lib.InvalidParameterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    out_str = json.dumps(report, ensure_ascii=False, indent=indent)
    print(out_str)

    if args.output_json:
        Path(args.output_json).write_text(out_str, encoding="utf-8")
        print(f"\nJSON written to: {args.output_json}", file=sys.stderr)

    # exit code: 0 if any importers, 1 if none（让脚本可被 shell 判断）
    return 0 if report.get("importers") else 1


if __name__ == "__main__":
    sys.exit(cli())
