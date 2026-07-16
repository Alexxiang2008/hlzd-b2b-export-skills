"""hlzd-pipeline-viz shared library.

消费 skills-demo trace JSON (或任一 Skill 的 trace), 累计指标并生成
self-contained HTML dashboard.

设计: stdlib only, 不接 D3.js (本地静态 HTML, 用 inline SVG 画漏斗).
"""
from __future__ import annotations

import html
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-pipeline-viz") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# Aggregation logic
# ================================================================

def _deep_find(d: Any, key: str) -> Optional[Any]:
    """Recursively search dict for key (useful for nested trace JSON)."""
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = _deep_find(v, key)
            if r is not None:
                return r
    elif isinstance(d, list):
        for item in d:
            r = _deep_find(item, key)
            if r is not None:
                return r
    return None


def aggregate_traces(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """消费多份 trace JSON, 累计指标。"""
    stages_total = Counter()
    stages_matched = Counter()
    grades = Counter()
    clearance = Counter()
    halted = 0
    halted_ids: List[str] = []
    actions_due: int = 0
    total_buyers: int = 0
    valid_buyers: int = 0
    followup_actions: int = 0
    knowledge_entities: int = 0
    quote_total_usd: float = 0.0
    quote_count: int = 0
    margins: List[float] = []
    negotiation_decisions: Counter = Counter()
    signal_origin: Counter = Counter()
    graph_total_nodes: int = 0
    graph_total_edges: int = 0
    sample_scenarios: List[Dict[str, str]] = []

    for t in traces:
        scenario_id = t.get("scenario_id", "")
        if scenario_id:
            sample_scenarios.append({
                "scenario_id": scenario_id,
                "stages_run": len(t.get("stages", {})),
            })
        stages = t.get("stages", {}) or {}
        for stage_name, stage_payload in stages.items():
            short = stage_name.split(":")[-1] if ":" in stage_name else stage_name
            stages_total[short] += 1
            if isinstance(stage_payload, dict):
                if stage_payload.get("matched") is True:
                    stages_matched[short] += 1
                # halt: 去重 (same stage's clearance + halt_recommended 双触发)
                halted_this_stage = False
                if "clearance" in stage_payload:
                    clearance[stage_payload["clearance"]] += 1
                    if stage_payload["clearance"] in ("PENDING_REVIEW", "BLOCKED"):
                        halted += 1
                        halted_this_stage = True
                        if scenario_id and scenario_id not in halted_ids:
                            halted_ids.append(scenario_id)
                if (not halted_this_stage
                    and stage_payload.get("halt_recommended", 0) > 0):
                    halted += 1
                    if scenario_id and scenario_id not in halted_ids:
                        halted_ids.append(scenario_id)
                if "company_grade" in stage_payload:
                    grades[stage_payload["company_grade"]] += 1
                if "incoterms" in stage_payload:
                    fob = stage_payload["incoterms"].get("FOB", {})
                    if "total_usd" in fob:
                        quote_total_usd += float(fob["total_usd"])
                        quote_count += 1
                if "profit_realized" in stage_payload:
                    r = stage_payload["profit_realized"].get("ratio")
                    if isinstance(r, (int, float)):
                        margins.append(float(r))
                if "decision" in stage_payload:
                    d = stage_payload["decision"]
                    if isinstance(d, dict) and "decision" in d:
                        negotiation_decisions[d["decision"]] += 1
                if "signals" in stage_payload and isinstance(stage_payload["signals"], list):
                    for s in stage_payload["signals"]:
                        if isinstance(s, dict) and "source" in s:
                            signal_origin[s["source"]] += 1
                if "graph" in stage_payload and isinstance(stage_payload["graph"], dict):
                    stats = stage_payload["graph"].get("stats", {})
                    graph_total_nodes += int(stats.get("node_count", 0))
                    graph_total_edges += int(stats.get("edge_count", 0))
                if "actions" in stage_payload and isinstance(stage_payload["actions"], list):
                    actions_due += len(stage_payload["actions"])
                if "extracted_entities" in stage_payload and isinstance(
                    stage_payload["extracted_entities"], dict):
                    for v in stage_payload["extracted_entities"].values():
                        if isinstance(v, list):
                            knowledge_entities += len(v)
                if "summary" in stage_payload and isinstance(stage_payload["summary"], dict):
                    if "total_emails" in stage_payload["summary"]:
                        total_buyers += int(stage_payload["summary"]["total_emails"])
                    if "actions_due" in stage_payload["summary"]:
                        followup_actions += int(stage_payload["summary"]["actions_due"])
                    if "actions_due" in stage_payload["summary"] and not stage_payload["summary"].get("by_stage"):
                        pass
        # 尝试捕获 overall valid / evaluated count
        evaluated = _deep_find(t, "evaluated")
        if isinstance(evaluated, int):
            valid_buyers = max(valid_buyers, evaluated)

    avg_margin = (sum(margins) / len(margins)) if margins else 0.0

    return {
        "traces_consumed": len(traces),
        "stages_total": dict(stages_total),
        "stages_matched": dict(stages_matched),
        "match_rate": {
            k: (stages_matched[k] / stages_total[k]) if stages_total.get(k, 0) > 0 else 0
            for k in stages_total
        },
        "grades": dict(grades),
        "clearance": dict(clearance),
        "halted_count": halted,
        "halted_scenario_ids": halted_ids,
        "actions_due": actions_due,
        "total_buyers": total_buyers,
        "valid_buyers": valid_buyers,
        "followup_actions": followup_actions,
        "knowledge_entities": knowledge_entities,
        "quote_count": quote_count,
        "quote_total_usd": round(quote_total_usd, 2),
        "avg_margin": round(avg_margin, 4),
        "margins_count": len(margins),
        "negotiation_decisions": dict(negotiation_decisions),
        "signal_origin": dict(signal_origin),
        "graph_total_nodes": graph_total_nodes,
        "graph_total_edges": graph_total_edges,
        "scenarios": sample_scenarios,
    }


# ================================================================
# Funnel SVG renderer (static, no D3)
# ================================================================

def render_funnel_svg(stages_total: Dict[str, int], max_width: int = 600,
                        row_height: int = 36) -> str:
    """简单漏斗: 按 stage 数量降序排列, 用 trapezoid 表示。"""
    if not stages_total:
        return '<svg width="600" height="60"><text x="20" y="30" fill="#888">no data</text></svg>'
    items = sorted(stages_total.items(), key=lambda x: -x[1])
    max_n = max(v for _, v in items) or 1
    total_h = len(items) * row_height + 16
    parts = [f'<svg width="{max_width}" height="{total_h}" xmlns="http://www.w3.org/2000/svg">']
    for i, (label, n) in enumerate(items):
        y = 8 + i * row_height
        w = max(40, int(max_width * 0.6 * n / max_n))
        x = (max_width - w) // 2
        opacity = 0.4 + 0.6 * (n / max_n)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{row_height-6}" '
            f'fill="#1e40af" opacity="{opacity:.2f}" rx="6"/>'
            f'<text x="{max_width//2}" y="{y+22}" text-anchor="middle" fill="#fff" '
            f'font-family="sans-serif" font-size="13">{_esc(label)} ({n})</text>'
        )
    parts.append('</svg>')
    return "\n".join(parts)


def render_bar_chart_svg(data: Dict[str, int], *, max_width: int = 400,
                          row_height: int = 24) -> str:
    """横向条形图 for grade / clearance / decisions。"""
    if not data:
        return '<svg width="400" height="60"><text x="20" y="30" fill="#888">no data</text></svg>'
    items = sorted(data.items(), key=lambda x: -x[1])
    max_n = max(v for _, v in items) or 1
    total_h = len(items) * row_height + 16
    parts = [f'<svg width="{max_width}" height="{total_h}" xmlns="http://www.w3.org/2000/svg">']
    for i, (label, n) in enumerate(items):
        y = 8 + i * row_height
        w = max(20, int((max_width - 100) * n / max_n))
        parts.append(
            f'<text x="4" y="{y+15}" fill="#333" font-family="sans-serif" font-size="12">{_esc(label)}</text>'
            f'<rect x="100" y="{y+2}" width="{w}" height="{row_height-6}" fill="#16a34a" rx="3"/>'
            f'<text x="{100+w+4}" y="{y+15}" fill="#333" font-family="sans-serif" font-size="11">{n}</text>'
        )
    parts.append('</svg>')
    return "\n".join(parts)


def _esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


# ================================================================
# HTML dashboard
# ================================================================

DASHBOARD_CSS = """
:root { --primary: #0f3460; --accent: #0891b2; --warn: #c2410c; --bg: #f8fafc; }
body { font-family: -apple-system, "Segoe UI", "PingFang SC", sans-serif;
       background: var(--bg); color: #1e293b; margin: 0; padding: 32px; }
h1 { color: var(--primary); border-bottom: 3px solid var(--accent); padding-bottom: 12px; }
h2 { color: var(--primary); margin-top: 32px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px; margin: 16px 0 32px; }
.kpi { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
       padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.kpi-value { font-size: 28px; font-weight: 900; color: var(--primary); }
.kpi-label { font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 24px 0; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; }
.warn { background: #fef3c7; border-left: 4px solid var(--warn);
        border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 16px 0; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
th { background: #f1f5f9; color: var(--primary); }
footer { margin-top: 64px; padding: 16px 0; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 12px; }
"""


def render_dashboard(agg: Dict[str, Any], *, title: str = "HLZD Pipeline Dashboard") -> str:
    s = agg
    funnel_svg = render_funnel_svg(s["stages_total"])
    grades_svg = render_bar_chart_svg(s["grades"])
    clearance_svg = render_bar_chart_svg(s["clearance"])
    decisions_svg = render_bar_chart_svg(s["negotiation_decisions"])

    halt_warning = ""
    if s["halted_count"] > 0:
        halt_warning = f"""<div class='warn'>
<strong>⚠ {s['halted_count']} halt(s) detected</strong> &nbsp;
Scenarios: {_esc(", ".join(s['halted_scenario_ids'][:5]))}
</div>"""

    scenarios_table = ""
    if s["scenarios"]:
        rows = "".join(
            f"<tr><td>{_esc(sc['scenario_id'])}</td><td>{sc['stages_run']}</td></tr>"
            for sc in s["scenarios"][:20]
        )
        scenarios_table = f"""
<table>
  <tr><th>Scenario</th><th>Stages run</th></tr>
  {rows}
</table>"""

    margin_text = (f"{s['avg_margin']*100:.1f}%" if s['margins_count'] else "n/a")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>{DASHBOARD_CSS}</style>
</head>
<body>
  <h1>{_esc(title)}</h1>
  <p>Traces consumed: <strong>{s['traces_consumed']}</strong> &middot; Stages tracked: <strong>{sum(s['stages_total'].values())}</strong></p>

  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-value">{s['traces_consumed']}</div><div class="kpi-label">Traces</div></div>
    <div class="kpi"><div class="kpi-value">{s['halted_count']}</div><div class="kpi-label">Halts</div></div>
    <div class="kpi"><div class="kpi-value">{s['actions_due']}</div><div class="kpi-label">Follow-up actions due</div></div>
    <div class="kpi"><div class="kpi-value">{s['valid_buyers']}</div><div class="kpi-label">Buyers evaluated</div></div>
    <div class="kpi"><div class="kpi-value">${s['quote_total_usd']:,.0f}</div><div class="kpi-label">Quote total (USD)</div></div>
    <div class="kpi"><div class="kpi-value">{margin_text}</div><div class="kpi-label">Avg margin</div></div>
    <div class="kpi"><div class="kpi-value">{s['knowledge_entities']}</div><div class="kpi-label">Knowledge entities</div></div>
    <div class="kpi"><div class="kpi-value">{s['graph_total_nodes']}/{s['graph_total_edges']}</div><div class="kpi-label">Graph nodes/edges</div></div>
  </div>

  {halt_warning}

  <h2>Pipeline Funnel</h2>
  <div class="row">
    <div class="card">{funnel_svg}</div>
  </div>

  <h2>Grade Distribution</h2>
  <div class="row">
    <div class="card">{grades_svg}</div>
    <div class="card">{clearance_svg}</div>
  </div>

  <h2>Negotiation Decisions</h2>
  <div class="row">
    <div class="card">{decisions_svg}</div>
  </div>

  <h2>Scenarios</h2>
  {scenarios_table}

  <footer>Generated by <code>hlzd-pipeline-viz</code> &middot; HLZD Cross-Border AI Platform</footer>
</body>
</html>
"""


# ================================================================
# Pipeline
# ================================================================

def run_pipeline(traces: List[Dict[str, Any]],
                   *, title: str = "HLZD Pipeline Dashboard") -> Dict[str, Any]:
    """End-to-end: aggregate traces + render dashboard."""
    if not isinstance(traces, list):
        raise TypeError("traces must be a list of dict")
    agg = aggregate_traces(traces)
    html_out = render_dashboard(agg, title=title)
    return {
        "$schema": "hlzd/pipeline-viz/v1",
        "aggregation": agg,
        "html_dashboard": html_out,
        "html_length": len(html_out),
    }
