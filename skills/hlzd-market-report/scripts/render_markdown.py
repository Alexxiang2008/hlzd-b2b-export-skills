"""hlzd-market-report Markdown renderer.

简化版：仅 8 节（除 cover 不分卡片），输出纯 Markdown，适合 GitHub / Lark / Notion。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def _render_cover(cover: Dict[str, Any], meta: Dict[str, Any]) -> str:
    if not cover:
        return ""
    title = cover.get("headline", "B2B Market Report")
    tagline = cover.get("tagline", "")
    topic = meta.get("topic", "")
    lines = [
        f"# {title}",
        "",
        f"> {tagline}" if tagline else "",
        "",
    ]
    if topic:
        lines.append(f"**Topic:** {topic}")
    kpis = cover.get("kpis", []) or []
    if kpis:
        lines.append("")
        lines.append("## KPI Snapshot")
        for k in kpis:
            lines.append(f"- **{k.get('value','')}** {k.get('unit','')} - {k.get('label','')}")
    plan = cover.get("three_step_plan", []) or []
    if plan:
        lines.append("")
        lines.append("## 3-Step Action Plan")
        for i, step in enumerate(plan, 1):
            lines.append(f"{i}. **{step.get('step','')}** - {step.get('action','')}")
    return "\n".join(l for l in lines if l) + "\n\n---\n\n"


def _render_toc(toc: List[Dict[str, Any]]) -> str:
    if not toc:
        return ""
    lines = ["## Table of Contents", ""]
    for i, t in enumerate(toc, 1):
        lines.append(f"{i}. {t.get('title','')}")
    return "\n".join(lines) + "\n\n---\n\n"


def _render_solution(sec: Dict[str, Any]) -> str:
    recap = sec.get("recap", "")
    lines = ["## 1. Solution Overview", "", f"{recap}", "", "| Metric | Finding | Implication |", "|---|---|---|"]
    for r in sec.get("conclusion_table", []) or []:
        lines.append(f"| {r.get('metric','')} | {r.get('finding','')} | {r.get('implication','')} |")
    return "\n".join(lines) + "\n\n---\n\n"


def _render_signals(sec: Dict[str, Any]) -> str:
    lines = ["## 2. 3 Core Signals", ""]
    for s in sec.get("signals", []) or []:
        lines.append(f"### {s.get('title','')}")
        lines.append("")
        lines.append(f"> {s.get('user_pain_quote','')}")
        lines.append("")
        lines.append(f"**Root cause:** {s.get('root_cause','')}")
        lines.append("")
        lines.append(f"**Market implication:** {s.get('market_implication','')}")
        lines.append("")
        src_html = []
        for src in s.get("sources", []) or []:
            src_html.append(lib.md_link(src.get("name","src"), src.get("url","")))
        if src_html:
            lines.append("Sources: " + " · ".join(src_html))
        lines.append("")
    return "\n".join(lines) + "---\n\n"


def _render_platforms(sec: Dict[str, Any]) -> str:
    lines = ["## 3. Platform Deep Dive", ""]
    for p in sec.get("platforms", []) or []:
        lines.append(f"### {p.get('name','')} - {p.get('stat','')}")
        lines.append("")
        for f in p.get("findings", []) or []:
            lines.append(f"- **{f.get('headline','')}** - {f.get('body','')} ({lib.md_link(f.get('source_name','src'), f.get('source_url',''))})")
        lines.append("")
    return "\n".join(lines) + "---\n\n"


def _render_comparison(sec: Dict[str, Any]) -> str:
    vendors = sec.get("vendors", []) or []
    attrs: List[str] = sec.get("attributes", []) or []
    if not vendors or not attrs:
        return "## 4. Strategic Comparison\n\n_No comparison data._\n\n---\n\n"
    lines = ["## 4. Strategic Comparison", "",
              "| Vendor | " + " | ".join(attrs) + " |",
              "|" + "|".join(["---"] * (len(attrs)+1)) + "|"]
    for v in vendors:
        row = [v.get("name","")]
        for a in attrs:
            row.append(str(v.get(a.lower().replace(" ", "_"), "-")))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n\n---\n\n"


def _render_actions(sec: Dict[str, Any]) -> str:
    lines = ["## 5. 3-Step Action Plan", ""]
    for i, a in enumerate(sec.get("actions", []) or [], 1):
        lines.append(f"### {i}. {a.get('title','')}")
        lines.append("")
        opts = a.get("options", []) or []
        if opts:
            for o in opts:
                lines.append(f"  - {o}")
            lines.append("")
        lines.append(f"**Execution:** {a.get('execution','')}")
        if a.get("risk"):
            lines.append(f"**Risk:** {a.get('risk','')}")
        lines.append("")
    return "\n".join(lines) + "---\n\n"


def _render_methodology(sec: Dict[str, Any]) -> str:
    lines = ["## 6. Methodology & Limitations", "",
              "### 5-Step Process", ""]
    for s in sec.get("five_step", []) or []:
        lines.append(f"1. {s}")
    lines.append("")
    lines.append("### 5-Dimension Signal Judgement")
    lines.append("")
    for s in sec.get("five_dim", []) or []:
        lines.append(f"1. {s}")
    lines.append("")
    limit = sec.get("seven_limitations", []) or []
    if limit:
        lines.append("### 7 Limitations")
        lines.append("")
        for s in limit:
            lines.append(f"- {s}")
        lines.append("")
    return "\n".join(lines) + "---\n\n"


def _render_sources(sec: Dict[str, Any]) -> str:
    src = sec.get("sources", []) or []
    if not src:
        return ""
    lines = ["## 7. Sources & Further Reading", ""]
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for s in src:
        by_cat.setdefault(s.get("category", "Other"), []).append(s)
    for cat, items in by_cat.items():
        lines.append(f"### {cat}")
        for s in items:
            lines.append(f"- {lib.md_link(s.get('name',''), s.get('url',''))}")
        lines.append("")
    return "\n".join(lines) + "---\n\n"


def render_markdown(report: Dict[str, Any]) -> str:
    meta = report.get("meta", {}) or {}
    parts = [
        _render_cover(report.get("cover", {}), meta),
        _render_toc(report.get("toc", [])),
        _render_solution(report.get("solution_overview", {})),
        _render_signals(report.get("three_signals", {})),
        _render_platforms(report.get("platform_deep_dive", {})),
        _render_comparison(report.get("strategic_comparison", {})),
        _render_actions(report.get("action_plan", {})),
        _render_methodology(report.get("methodology", {})),
        _render_sources(report.get("footer_sources", {})),
    ]
    return "".join(parts)


def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="hlzd-market-report-render-md")
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o")
    args = parser.parse_args()
    raw = Path(args.input).read_text(encoding="utf-8")
    report = json.loads(raw)
    out = render_markdown(report)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"Markdown written: {args.output} ({len(out)} bytes)", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
