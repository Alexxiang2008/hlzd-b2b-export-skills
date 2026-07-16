#!/usr/bin/env python3
"""hlzd-knowledge-graph CLI.

输入：free text (e.g. inquiry text) 或 JSON
输出：JSON {extracted_entities, graph, queries}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-knowledge-graph")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--input", "-i", help="Path to text file (or JSON with 'text' key)")
    grp.add_argument("--stdin", "-s", action="store_true")
    parser.add_argument("--text", help="Raw text directly")
    parser.add_argument("--customer", help="Customer name to anchor graph")
    parser.add_argument("--customer-id", help="Customer node id (default slug)")
    parser.add_argument("--query-product", help="Query: customers for this product")
    parser.add_argument("--query-country", help="Query: products in this country")
    parser.add_argument("--dot", action="store_true", help="Output DOT (graphviz) instead of JSON")
    parser.add_argument("--output", "-o", help="Output path")
    parser.add_argument("--pretty", "-p", action="store_true")
    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.stdin:
        text = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
            text = data.get("text", raw) if isinstance(data, dict) else raw
        except json.JSONDecodeError:
            text = raw

    if args.dot:
        # DOT mode: extract entities → build graph → render DOT
        from lib import extract_entities, build_graph_from_entities, export_dot
        ents = extract_entities(text)
        g = build_graph_from_entities(ents, customer_name=args.customer,
                                       customer_id=args.customer_id)
        print(export_dot(g))
        return 0

    result = lib.run_pipeline(text, customer_name=args.customer,
                                customer_id=args.customer_id,
                                query_product=args.query_product,
                                query_country=args.query_country)

    indent = 2 if args.pretty else None
    out_str = json.dumps(result, ensure_ascii=False, indent=indent)
    print(out_str)
    if args.output:
        Path(args.output).write_text(out_str, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
