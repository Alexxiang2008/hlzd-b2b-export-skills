"""hlzd-market-report HTML renderer.

Input schema (dict)：
{
  "meta": { "topic": str, "audience": str, "window_days": int, "language": str },
  "cover": { "headline": str, "tagline": str,
              "kpis": [ {"label": str, "value": str, "unit": str?}, ... ],
              "three_step_plan": [ {"step": str, "action": str}, ... ] },
  "toc": [ {"id": str, "title": str}, ... ],
  "solution_overview": {
    "recap": str,
    "conclusion_table": [ {"metric": str, "finding": str, "implication": str}, ... ] },
  "three_signals": {
    "signals": [
      { "title": str, "user_pain_quote": str, "root_cause": str,
        "market_implication": str, "sources": [ {"name": str, "url": str}, ... ] },
      ... ] },
  "platform_deep_dive": {
    "platforms": [
      { "name": str, "stat": str,
        "findings": [ {"headline": str, "body": str, "source_name": str, "source_url": str},
                     ... ] },
      ... ] },
  "strategic_comparison": {
    "vendors": [ { "name": str, "attribute_1": str, ... }, ... ],
    "attributes": [str, ...]  // column headers
  },
  "action_plan": {
    "actions": [
      { "title": str, "options": [str, ...], "risk": str, "execution": str },
      ... ] },
  "methodology": {
    "five_step": [str, ...],
    "five_dim": [str, ...],
    "seven_limitations": [str, ...]
  },
  "footer_sources": {
    "sources": [ {"name": str, "url": str, "category": str}, ... ]
  }
}

Output: a single self-contained HTML file string (CSS inlined).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


# ================================================================
# 1. CSS (HLZD 工业品出海上色)
# ================================================================

CSS = """
:root {
  --primary: #0f3460;
  --accent: #0891b2;
  --warning: #c2410c;
  --success: #16a34a;
  --ink: #1e293b;
  --ink-light: #475569;
  --muted: #64748b;
  --bg: #f8fafc;
  --bg-alt: #f1f5f9;
  --card: #ffffff;
  --border: #e2e8f0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  font-size: 16px;
  line-height: 1.7;
  color: var(--ink);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
}
.container { max-width: 1100px; margin: 0 auto; padding: 0 32px; }
h1, h2, h3, h4 { color: var(--ink); font-weight: 800; letter-spacing: -0.5px; }
h2 { font-size: 32px; margin: 56px 0 16px; }
h3 { font-size: 22px; margin: 32px 0 12px; color: var(--primary); }
h4 { font-size: 18px; margin: 16px 0 8px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* cover */
.cover {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0891b2 100%);
  color: white;
  padding: 80px 0;
}
.cover-headline {
  font-size: 56px; font-weight: 900; line-height: 1.1;
  letter-spacing: -2px; max-width: 1000px; margin-bottom: 24px;
}
.cover-tagline {
  font-size: 18px; opacity: 0.85; margin-bottom: 48px;
  max-width: 700px;
}
.cover-tag {
  display: inline-block; padding: 6px 14px;
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);
  border-radius: 100px; font-size: 13px; font-weight: 500;
  letter-spacing: 0.5px; margin-bottom: 32px;
}

/* KPI cards */
.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px; margin: 32px 0;
}
.kpi-card {
  background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
  border-radius: 12px; padding: 20px;
  backdrop-filter: blur(10px);
}
.kpi-value { font-size: 36px; font-weight: 900; line-height: 1; }
.kpi-label { font-size: 13px; opacity: 0.8; margin-top: 6px; }

/* Action cards (L1) */
.action-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px; margin: 32px 0;
}
.action-card {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #1e293b; border-radius: 12px; padding: 24px;
  font-weight: 700;
}
.action-card h4 { color: #1e293b; margin-bottom: 8px; }
.action-card .step-num {
  display: inline-block; width: 32px; height: 32px; line-height: 32px;
  text-align: center; background: rgba(0,0,0,0.1); border-radius: 50%;
  margin-right: 8px;
}

/* TOC */
.toc { background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; padding: 24px; margin: 32px 0; }
.toc ol { padding-left: 24px; }
.toc li { margin: 6px 0; }

/* Signal cards */
.signal-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; padding: 24px; margin: 16px 0;
  box-shadow: 0 1px 4px rgba(15,23,42,0.04);
}
.signal-quote {
  border-left: 3px solid var(--warning); padding: 12px 16px;
  background: var(--bg-alt); border-radius: 0 8px 8px 0;
  font-style: italic; margin: 12px 0;
}
.signal-source {
  display: inline-block; padding: 4px 10px;
  background: var(--bg-alt); border-radius: 100px;
  font-size: 13px; margin-right: 8px;
}

/* Platform cards */
.platform-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; padding: 24px; margin: 16px 0;
}
.platform-stat {
  display: inline-block; padding: 4px 12px;
  background: var(--primary); color: white;
  border-radius: 100px; font-size: 13px; margin-bottom: 12px;
}
.platform-findings { list-style: none; padding: 0; }
.platform-findings li { margin: 8px 0; padding-left: 16px; position: relative; }
.platform-findings li::before {
  content: '→'; position: absolute; left: 0; color: var(--accent);
}

/* Comparison table */
table {
  width: 100%; border-collapse: collapse; margin: 24px 0;
  background: var(--card); border-radius: 8px; overflow: hidden;
  box-shadow: 0 1px 4px rgba(15,23,42,0.04);
}
th, td {
  padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border);
}
th { background: var(--bg-alt); font-weight: 700; color: var(--primary); }
tr:hover { background: var(--bg-alt); }

/* Action plan */
.action-plan-card {
  background: var(--card); border-left: 4px solid var(--success);
  border-radius: 0 8px 8px 0; padding: 20px; margin: 16px 0;
}
.risk-tag {
  display: inline-block; padding: 2px 10px; background: var(--warning);
  color: white; border-radius: 100px; font-size: 12px; margin-top: 8px;
}

/* Methodology */
.methodology-callout {
  background: #fef3c7; border-left: 4px solid var(--warning);
  padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 16px 0;
}

/* Sources */
.sources-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px; margin: 24px 0;
}
.source-link {
  display: block; padding: 10px 14px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: 8px; font-size: 14px;
}
.source-link:hover { background: var(--bg-alt); }

/* Footer */
footer {
  margin-top: 64px; padding: 32px 0; background: var(--ink);
  color: rgba(255,255,255,0.7); font-size: 13px;
  text-align: center;
}

@media print {
  body { background: white; }
  .cover { background: white; color: var(--ink); border-bottom: 4px solid var(--primary); padding: 32px 0; }
  .kpi-card, .action-card { background: white; border: 1px solid var(--border); color: var(--ink); }
  footer { background: white; color: var(--muted); border-top: 1px solid var(--border); }
}
"""


# ================================================================
# 2. Section renderers
# ================================================================

def _render_cover(cover: Dict[str, Any], meta: Dict[str, Any]) -> str:
    if not cover:
        return ""
    headline = lib.normalize_dashes(lib.esc(cover.get("headline", "B2B Overseas Market Report")))
    tagline = lib.normalize_dashes(lib.esc(cover.get("tagline", "")))
    topic = lib.esc(meta.get("topic", "")) if meta else ""
    audience = lib.esc(meta.get("audience", "B2B Cross-Border Business Leads")) if meta else ""
    window = meta.get("window_days", 30) if meta else 30
    language = lib.esc(meta.get("language", "en")) if meta else "en"

    kpis_html = ""
    for kpi in cover.get("kpis", []) or []:
        val = lib.esc(kpi.get("value", ""))
        lab = lib.esc(kpi.get("label", ""))
        unit = lib.esc(kpi.get("unit", ""))
        kpis_html += f"""
        <div class="kpi-card">
          <div class="kpi-value">{val}<span style="font-size:14px;opacity:0.7;"> {unit}</span></div>
          <div class="kpi-label">{lab}</div>
        </div>"""

    plan_html = ""
    for i, step in enumerate(cover.get("three_step_plan", []) or [], 1):
        step_text = lib.esc(step.get("step", f"Step {i}"))
        action_text = lib.esc(step.get("action", ""))
        plan_html += f"""
        <div class="action-card">
          <h4><span class="step-num">{i}</span>{step_text}</h4>
          <p>{action_text}</p>
        </div>"""

    meta_html = f"""
    <div style="font-size:13px;opacity:0.7;margin-top:24px;">
      Topic: <strong>{topic}</strong> &nbsp;·&nbsp;
      Window: last {window} days &nbsp;·&nbsp;
      Language: {language} &nbsp;·&nbsp;
      Audience: {audience}
    </div>"""

    return f"""
<section class="cover">
  <div class="container">
    <span class="cover-tag">HLZD B2B Industrial Export · Market Intelligence</span>
    <h1 class="cover-headline">{headline}</h1>
    <p class="cover-tagline">{tagline}</p>
    <div class="kpi-grid">{kpis_html}</div>
    <h2 style="color:white;border:none;margin-top:32px;">Action Plan</h2>
    <div class="action-grid">{plan_html}</div>
    {meta_html}
  </div>
</section>
"""


def _render_toc(toc: List[Dict[str, Any]]) -> str:
    if not toc:
        return ""
    items = "".join(
        f'<li><a href="#sec-{lib.esc(item.get("id", str(i)))}">'
        f'{lib.esc(item.get("title", ""))}</a></li>'
        for i, item in enumerate(toc)
    )
    return f"""
<section class="container">
  <h2 id="sec-toc">Table of Contents</h2>
  <div class="toc"><ol>{items}</ol></div>
</section>
"""


def _render_solution_overview(sec: Dict[str, Any]) -> str:
    recap = lib.normalize_dashes(lib.esc(sec.get("recap", "")))
    rows_html = ""
    for row in sec.get("conclusion_table", []) or []:
        rows_html += "<tr>"
        for k in ("metric", "finding", "implication"):
            rows_html += f"<td>{lib.esc(row.get(k, ''))}</td>"
        rows_html += "</tr>"
    return f"""
<section class="container">
  <h2 id="sec-solution">Solution Overview</h2>
  <p style="font-size:18px;color:var(--ink-light);">{recap}</p>
  <table>
    <thead><tr><th>Metric</th><th>Finding</th><th>Implication</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</section>
"""


def _render_three_signals(sec: Dict[str, Any]) -> str:
    cards_html = ""
    for s in (sec.get("signals") or []):
        title = lib.esc(s.get("title", ""))
        quote = lib.normalize_dashes(lib.esc(s.get("user_pain_quote", "")))
        root = lib.normalize_dashes(lib.esc(s.get("root_cause", "")))
        impl = lib.normalize_dashes(lib.esc(s.get("market_implication", "")))
        sources_html = ""
        for src in s.get("sources", []) or []:
            name = lib.esc(src.get("name", ""))
            url = lib.url_href(src.get("url", ""))
            sources_html += f'<a class="signal-source" href="{url}" target="_blank" rel="noopener">{name}</a>'
        cards_html += f"""
        <div class="signal-card">
          <h3>{title}</h3>
          <div class="signal-quote">{quote}</div>
          <p><strong>Root cause:</strong> {root}</p>
          <p><strong>Market implication:</strong> {impl}</p>
          <div style="margin-top:12px;">{sources_html}</div>
        </div>
        """
    return f"""
<section class="container">
  <h2 id="sec-signals">3 Core Signals</h2>
  {cards_html}
</section>
"""


def _render_platform_deep_dive(sec: Dict[str, Any]) -> str:
    cards = ""
    for p in (sec.get("platforms") or []):
        name = lib.esc(p.get("name", ""))
        stat = lib.esc(p.get("stat", ""))
        findings_html = ""
        for f in p.get("findings", []) or []:
            headline = lib.normalize_dashes(lib.esc(f.get("headline", "")))
            body = lib.normalize_dashes(lib.esc(f.get("body", "")))
            sname = lib.esc(f.get("source_name", ""))
            surl = lib.url_href(f.get("source_url", ""))
            findings_html += f"""
            <li>
              <strong>{headline}</strong> - {body}
              <br><a href="{surl}" target="_blank" rel="noopener" style="font-size:13px;">[{sname}]</a>
            </li>"""
        cards += f"""
        <div class="platform-card">
          <div class="platform-stat">{name} - {stat}</div>
          <ul class="platform-findings">{findings_html}</ul>
        </div>
        """
    return f"""
<section class="container">
  <h2 id="sec-platforms">Platform Deep Dive</h2>
  {cards}
</section>
"""


def _render_strategic_comparison(sec: Dict[str, Any]) -> str:
    vendors = sec.get("vendors", []) or []
    attributes: List[str] = sec.get("attributes", []) or []
    if not vendors or not attributes:
        return f"""
<section class="container">
  <h2 id="sec-comparison">Strategic Comparison</h2>
  <p style="color:var(--muted);font-style:italic;">No comparison data provided.</p>
</section>
"""
    header_cells = "<th>Vendor</th>" + "".join(f"<th>{lib.esc(a)}</th>" for a in attributes)
    rows_html = ""
    for v in vendors:
        cells = f"<td><strong>{lib.esc(v.get('name', ''))}</strong></td>"
        for a in attributes:
            cells += f"<td>{lib.esc(v.get(a.lower().replace(' ', '_'), '-'))}</td>"
        rows_html += f"<tr>{cells}</tr>"
    return f"""
<section class="container">
  <h2 id="sec-comparison">Strategic Comparison Table</h2>
  <table>
    <thead><tr>{header_cells}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</section>
"""


def _render_action_plan(sec: Dict[str, Any]) -> str:
    cards_html = ""
    for i, action in enumerate(sec.get("actions", []) or [], 1):
        title = lib.normalize_dashes(lib.esc(action.get("title", f"Action {i}")))
        risk = lib.esc(action.get("risk", ""))
        execution = lib.normalize_dashes(lib.esc(action.get("execution", "")))
        options = action.get("options", []) or []
        options_html = ""
        if options:
            opts = "<br>".join(f"&nbsp; - {lib.normalize_dashes(lib.esc(o))}" for o in options)
            options_html = f"<p><strong>Options:</strong><br>{opts}</p>"
        risk_html = f'<span class="risk-tag">Risk: {risk}</span>' if risk else ""
        cards_html += f"""
        <div class="action-plan-card">
          <h4>{i}. {title}</h4>
          {options_html}
          <p>{execution}</p>
          {risk_html}
        </div>"""
    return f"""
<section class="container">
  <h2 id="sec-actions">3-Step Action Plan</h2>
  {cards_html}
</section>
"""


def _render_methodology(sec: Dict[str, Any]) -> str:
    five_steps = "".join(f"<li>{lib.normalize_dashes(lib.esc(s))}</li>" for s in sec.get("five_step", []) or [])
    five_dim = "".join(f"<li>{lib.normalize_dashes(lib.esc(s))}</li>" for s in sec.get("five_dim", []) or [])
    limit = "".join(f"<li>{lib.normalize_dashes(lib.esc(s))}</li>" for s in sec.get("seven_limitations", []) or [])
    return f"""
<section class="container">
  <h2 id="sec-methodology">Methodology &amp; Limitations</h2>
  <h3>5-Step Process</h3>
  <ol>{five_steps}</ol>
  <h3>5-Dimension Signal Judgement</h3>
  <ol>{five_dim}</ol>
  <div class="methodology-callout">
    <strong>Limitations (7):</strong>
    <ol>{limit}</ol>
  </div>
</section>
"""


def _render_footer_sources(sec: Dict[str, Any]) -> str:
    src = sec.get("sources", []) or []
    if not src:
        return ""
    items_html = ""
    for s in src:
        name = lib.esc(s.get("name", ""))
        url = lib.url_href(s.get("url", ""))
        cat = lib.esc(s.get("category", ""))
        items_html += f'<a class="source-link" href="{url}" target="_blank" rel="noopener">{cat}: {name}</a>'
    return f"""
<section class="container" id="sec-sources">
  <h2>Sources &amp; Further Reading</h2>
  <div class="sources-grid">{items_html}</div>
</section>
"""


# ================================================================
# 3. 主入口
# ================================================================

def render_html(report: Dict[str, Any]) -> str:
    meta = report.get("meta", {}) or {}
    topic = lib.esc(meta.get("topic", "B2B Market Report"))
    audience = lib.esc(meta.get("audience", "B2B Cross-Border Business Leads"))

    sections_html = "".join([
        _render_cover(report.get("cover", {}), meta),
        _render_toc(report.get("toc", [])),
        _render_solution_overview(report.get("solution_overview", {})),
        _render_three_signals(report.get("three_signals", {})),
        _render_platform_deep_dive(report.get("platform_deep_dive", {})),
        _render_strategic_comparison(report.get("strategic_comparison", {})),
        _render_action_plan(report.get("action_plan", {})),
        _render_methodology(report.get("methodology", {})),
        _render_footer_sources(report.get("footer_sources", {})),
    ])

    footer = f"""
<footer>
  <div class="container">
    <p>Generated by <strong>HLZD Cross-Border AI Platform</strong> - 2026</p>
    <p style="margin-top:8px;">This report is a heuristic starting point - validate key claims with primary sources before commercial action.</p>
    <p style="margin-top:8px;">License: MIT &nbsp;·&nbsp; Contact: research@hlzd.example.com</p>
  </div>
</footer>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{topic} - HLZD Market Intelligence</title>
<style>{CSS}</style>
</head>
<body>
{sections_html}
{footer}
</body>
</html>
"""


# ================================================================
# 4. CLI
# ================================================================

def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="hlzd-market-report-render-html")
    parser.add_argument("--input", "-i", required=True, help="Path to report.json")
    parser.add_argument("--output", "-o", help="Output HTML file path (default stdout)")
    args = parser.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8")
    report = json.loads(raw)

    # 校验（仅警告，不阻断）
    errors = lib.validate_schema(report)
    if errors:
        print(f"warn: schema has {len(errors)} issues", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)

    html_out = render_html(report)

    if args.output:
        Path(args.output).write_text(html_out, encoding="utf-8")
        print(f"HTML written: {args.output} ({len(html_out)} bytes)", file=sys.stderr)
    else:
        print(html_out)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
