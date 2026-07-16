#!/usr/bin/env python3
"""hlzd-pipeline-viz CLI.

输入：1+ trace JSON（来自 skills-demo/outputs/*.json）
输出：self-contained HTML dashboard
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-pipeline-viz")
    parser.add_argument("--input", "-i", action="append", required=True,
                         help="Path to a trace JSON (repeatable)")
    parser.add_argument("--title", default="HLZD Pipeline Dashboard")
    parser.add_argument("--output", "-o", help="Output HTML path")
    args = parser.parse_args()

    traces: List[dict] = []
    for path in args.input:
        with open(path, encoding="utf-8") as f:
            traces.append(json.load(f))

    if not traces:
        print("error: no input traces", file=sys.stderr)
        return 1

    result = lib.run_pipeline(traces, title=args.title)
    if args.output:
        Path(args.output).write_text(result["html_dashboard"], encoding="utf-8")
        print(f"written: {args.output} ({result['html_length']} bytes)",
              file=sys.stderr)
    else:
        print(result["html_dashboard"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
