#!/usr/bin/env python3
"""hlzd-followup-sequencer CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-followup-sequencer")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--input", "-i", help="Path to outreach JSON")
    grp.add_argument("--stdin", "-s", action="store_true")
    parser.add_argument("--output", "-o", help="Output report path")
    parser.add_argument("--pretty", "-p", action="store_true")
    parser.add_argument("--as-of", help="Override 'now' date (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.stdin:
        raw = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")
    data = json.loads(raw)
    emails = data if isinstance(data, list) else data.get("emails", [])
    if not isinstance(emails, list):
        print("error: input must be list or dict with 'emails' key", file=sys.stderr)
        return 1

    now = None
    if args.as_of:
        from datetime import datetime, timezone
        now = datetime.strptime(args.as_of, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    try:
        report = lib.run_sequencer(emails, now=now)
    except lib.FollowupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    out_str = json.dumps(report, ensure_ascii=False, indent=indent)
    print(out_str)
    if args.output:
        Path(args.output).write_text(out_str, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)
    return 0 if report["summary"]["actions_due"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
