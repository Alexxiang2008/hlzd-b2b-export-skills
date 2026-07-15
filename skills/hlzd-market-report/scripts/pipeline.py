"""hlzd-market-report pipeline orchestrator.

提供：
- assemble_report(data) → 把任意数据补全为 9 节 report schema
- from_research(b2b_research_json) → 把 hlzd-b2b-research 输出转 report schema
- run(topic, keywords, country, output_html, output_md) → 一键出报告

设计：v0.1 pipeline orchestrator 不做 LLM 调用，纯 deterministic assembler。
LLM 增强（如把 raw signals 提炼成 3 core signals）留给上层 Agent。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402
import render_html  # noqa: E402
import render_markdown  # noqa: E402
import collect_web  # noqa: E402


def _now_window(window_days: int) -> str:
    end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start = (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=window_days)).strftime("%Y-%m-%d")
    return f"{start} to {end}"


def assemble_report(
    *,
    topic: str,
    audience: str = "B2B Cross-Border Business Leads",
    window_days: int = 30,
    language: str = "en",
    cover: Optional[Dict[str, Any]] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    platforms: Optional[List[Dict[str, Any]]] = None,
    vendors: Optional[List[Dict[str, Any]]] = None,
    attributes: Optional[List[str]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """把外部数据组装成 9 节 report schema。

    各 section 缺失时给 fallback（empty 占位），不阻断。
    """
    sig_list = signals or []

    # 自动提炼 signals（heuristic）：取前 3 个作为"3 Core Signals"
    three_signals_data = []
    for sig in sig_list[:3]:
        three_signals_data.append({
            "title": sig.get("title", "")[:80],
            "user_pain_quote": sig.get("snippet", sig.get("title", ""))[:200],
            "root_cause": lib.normalize_dashes(sig.get("root_cause", "see source")),
            "market_implication": lib.normalize_dashes(sig.get("market_implication", "see source")),
            "sources": [{"name": sig.get("source", "source"), "url": sig.get("url", "")}],
        })
    if not three_signals_data:
        three_signals_data = [{
            "title": "No signals collected (set HLZD_BRAVE_API_KEY or pip install ddgs)",
            "user_pain_quote": "Manual signal collection recommended",
            "root_cause": "Web data source not configured",
            "market_implication": "Re-run with proper data source",
            "sources": [],
        }]

    # fallback cover
    cover_default = {
        "headline": f"{topic} - B2B Market Intelligence",
        "tagline": (f"A 30-day market scan for {audience}, focused on cross-border "
                     f"industrial export opportunities."),
        "kpis": [
            {"label": "Window", "value": window_days, "unit": "days"},
            {"label": "Signals collected", "value": len(sig_list), "unit": ""},
            {"label": "Topics scanned", "value": 1, "unit": ""},
            {"label": "Audience", "value": "B2B leads", "unit": ""},
        ],
        "three_step_plan": actions[:3] if actions else [
            {"step": "Run market research", "action": "Use hlzd-b2b-research to scan HS codes + market size"},
            {"step": "Find overseas buyers", "action": "Use hlzd-buyer-finder to discover importers"},
            {"step": "Generate HTML report", "action": "Re-run this Skill with richer signal source"},
        ],
    }
    if cover:
        cover_default.update(cover)

    toc = [
        {"id": "toc", "title": "Table of Contents"},
        {"id": "solution", "title": "Solution Overview"},
        {"id": "signals", "title": "3 Core Signals"},
        {"id": "platforms", "title": "Platform Deep Dive"},
        {"id": "comparison", "title": "Strategic Comparison"},
        {"id": "actions", "title": "3-Step Action Plan"},
        {"id": "methodology", "title": "Methodology & Limitations"},
        {"id": "sources", "title": "Sources"},
    ]

    platforms_default = []
    if platforms:
        platforms_default = platforms
    elif sig_list:
        # 把 signals 按 source 字段分组
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for s in sig_list:
            groups.setdefault(s.get("source", "Web"), []).append(s)
        for source, items in groups.items():
            platforms_default.append({
                "name": source,
                "stat": f"{len(items)} results",
                "findings": [{
                    "headline": i.get("title", "")[:80],
                    "body": i.get("snippet", "")[:160],
                    "source_name": i.get("source", "source"),
                    "source_url": i.get("url", ""),
                } for i in items[:5]],
            })

    if not vendors:
        vendors = [
            {"name": "Local Supplier (placeholder)",
             "hs_coverage": "-", "lead_time": "-", "moq": "-",
             "certifications": "-", "avg_price": "-", "incoterms": "-",
             "online_presence": "-", "exhibitions": "-", "reviews": "-", "trust_score": "-"},
            {"name": "Your Solution",
             "hs_coverage": "-", "lead_time": "-", "moq": "-",
             "certifications": "-", "avg_price": "-", "incoterms": "-",
             "online_presence": "-", "exhibitions": "-", "reviews": "-", "trust_score": "-"},
            {"name": "Alternative Vendor (placeholder)",
             "hs_coverage": "-", "lead_time": "-", "moq": "-",
             "certifications": "-", "avg_price": "-", "incoterms": "-",
             "online_presence": "-", "exhibitions": "-", "reviews": "-", "trust_score": "-"},
        ]
    if not attributes:
        attributes = ["HS Coverage", "Lead Time", "MOQ", "Certifications",
                       "Avg Price", "Incoterms", "Online Presence",
                       "Exhibitions", "Reviews", "Trust Score"]

    actions_default = actions or [
        {"title": "Run market validation",
         "options": ["Use hlzd-b2b-research for HS + Comtrade", "Use hlzd-buyer-finder for importers"],
         "risk": "Time cost 4-8 hours; potential API rate limits.",
         "execution": "Run both pipelines in parallel; cross-validate HS coding coverage."},
        {"title": "Outreach 10 priority buyers",
         "options": ["Email via hlzd-cold-outreach (Week 8)", "LinkedIn direct message (manual)"],
         "risk": "Low reply rate (~5-10%) without warm introduction.",
         "execution": "Prepare 10 tailored RFQ-followup packs; send via personalized email per buyer."},
        {"title": "Set up trade-compliance gate",
         "options": ["HLZD-trades-compliance Skill (W8)", "Manual broker review for first 3 deals"],
         "risk": "Regulatory mis-step on OCTG / dual-use can halt shipment at customs.",
         "execution": "Pre-clear HS, sanctions, dual-use for every new lead before quoting."},
    ]

    # 收集所有 sources（去重）
    seen_sources: set = set()
    sources_default = []
    for sig in sig_list:
        url = sig.get("url", "")
        if url and url not in seen_sources:
            seen_sources.add(url)
            sources_default.append({
                "name": sig.get("title", "")[:60],
                "url": url,
                "category": sig.get("source", "Web"),
            })
    if sources:
        sources_default = sources

    return {
        "$schema": "hlzd/market-report/v1",
        "meta": {
            "topic": topic,
            "audience": audience,
            "window_days": window_days,
            "language": language,
            "generated_at_utc": lib.utc_now_iso(),
            "window": _now_window(window_days),
        },
        "cover": cover_default,
        "toc": toc,
        "solution_overview": {
            "recap": (f"Thirty-day cross-border scan surfaces {len(sig_list)} candidate signals "
                       f"around {topic}; readers can use the action plan to prioritize next moves."),
            "conclusion_table": [
                {"metric": "Signals collected", "finding": f"{len(sig_list)} raw + {len(three_signals_data)} curated",
                 "implication": "Sufficient breadth for first-pass validation"},
                {"metric": "Data sources", "finding": "1-2 (Web + optional DDGS)",
                 "implication": "Add LinkedIn / 海关数据 for richer evidence in v0.2"},
                {"metric": "Confidence", "finding": "Heuristic, not authoritative",
                 "implication": "All claims must be re-verified before commercial decision"},
                {"metric": "Update cadence", "finding": "Re-run weekly",
                 "implication": "Pipeline is deterministic; share state across runs"},
                {"metric": "Best-action", "finding": "Review 3 signals + 3 actions first",
                 "implication": "Filters out noise for first-30-min review"},
            ],
        },
        "three_signals": {"signals": three_signals_data},
        "platform_deep_dive": {"platforms": platforms_default},
        "strategic_comparison": {"vendors": vendors, "attributes": attributes},
        "action_plan": {"actions": actions_default},
        "methodology": {
            "five_step": [
                "Topic scoping + audience definition (top-of-funnel)",
                "Data source activation (Brave / ddgs / internal skills)",
                "Signal collection with rate limits + dedup",
                "5-dimension signal judgement (heuristic, not authoritative)",
                "Render: HTML single-file + Markdown 8-section",
            ],
            "five_dim": [
                "30-day activity volume (engagement numbers in window)",
                "Cross-source consensus (>=2 independent sources)",
                "Time freshness (2026-dated, not cached 2024 data)",
                "Engagement strength (composite of upvotes / likes / views)",
                "Cross-platform (same trend surfaces in >=3 platforms)",
            ],
            "seven_limitations": [
                "Heuristic scoring is qualitative, not quantitative forecast.",
                "Web signals may lag real-world adoption by 1-3 months.",
                "Language coverage is en + zh + es; ar / ru / pt excluded in v0.1.",
                "Pricing data is qualitative reference only (no real-time quotes).",
                "Buyer-side contact info is platform-dependent; many platforms mask email.",
                "No LLM enhancement in pipeline output; curated signals may be templated.",
                "Self-audit signal judgement is required before commercial action.",
            ],
        },
        "footer_sources": {"sources": sources_default},
    }


def from_b2b_research(research_json: Dict[str, Any]) -> Dict[str, Any]:
    """把 hlzd-b2b-research 输出转 market-report schema。

    Input shape: {product, markets, hs_code_used, hs_code_candidates,
                   trade_data, trends, buyers, warnings}
    """
    product = research_json.get("product", "B2B Industrial Product")
    markets = research_json.get("markets", [])
    warnings = research_json.get("warnings", [])

    # 用 trade_data 当 "3 core signals"
    signals = []
    for m, data in research_json.get("trade_data", {}).items():
        if not isinstance(data, dict) or not data.get("countries"):
            continue
        top = data["countries"][0] if data["countries"] else {}
        signals.append({
            "title": f"{m}: top supplier is {top.get('country','?')}",
            "snippet": f"Imports ~${data.get('total_import_value_usd',0)/1e6:.1f}M USD, "
                       f"{top.get('country','?')} {top.get('share_pct',0):.1f}% share.",
            "url": "",
            "source": "UN Comtrade",
            "root_cause": f"Top supplier dominates {data.get('total_import_value_usd',0)/1e6:.0f}M of imports.",
            "market_implication": f"HS {data.get('hs_code','?')} in {m}: explore competitive positioning vs {top.get('country','?')}.",
        })
    sources = [s for s in signals if s.get("url")]
    return assemble_report(
        topic=f"{product} cross-border market scan",
        cover={
            "headline": f"{product} - Cross-Border Market Scan ({', '.join(markets)})",
            "tagline": f"Pipeline data drawn from hlzd-b2b-research. Window: 12 months.",
            "kpis": [
                {"label": "Markets scanned", "value": len(markets), "unit": ""},
                {"label": "HS code used", "value": research_json.get("hs_code_used") or "?", "unit": ""},
                {"label": "Trade records", "value": sum(len(d.get("countries",[])) for d in research_json.get("trade_data",{}).values() if isinstance(d, dict)), "unit": ""},
                {"label": "Warnings", "value": len(warnings), "unit": ""},
            ],
        },
        signals=signals,
        sources=sources,
        vendors=[
            {"name": "Local Supplier", "hs_coverage": "?"},
            {"name": "Your Solution", "hs_coverage": str(research_json.get("hs_code_used", "?"))},
            {"name": "Alternative", "hs_coverage": "?"},
        ],
    )


def run(
    topic: str,
    keywords: Optional[List[str]] = None,
    *,
    audience: str = "B2B Cross-Border Business Leads",
    window_days: int = 30,
    output_html: Optional[str] = None,
    output_md: Optional[str] = None,
    collect_method: str = "auto",
    b2b_research_input: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """一键出报告：collect → assemble → render 两个格式。

    Returns the assembled report dict.
    """
    if b2b_research_input:
        report = from_b2b_research(b2b_research_input)
    else:
        signals, warns = collect_web.collect_signals(keywords or [topic],
                                                       window_days=window_days,
                                                       method=collect_method)
        report = assemble_report(
            topic=topic,
            audience=audience,
            window_days=window_days,
            signals=signals,
        )
        # attach collector warnings to meta for transparency
        report["meta"]["collector_warnings"] = warns

    html_out = render_html.render_html(report)
    md_out = render_markdown.render_markdown(report)

    if output_html:
        Path(output_html).write_text(html_out, encoding="utf-8")
    if output_md:
        Path(output_md).write_text(md_out, encoding="utf-8")

    return report


# ================================================================
# CLI
# ================================================================

def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="hlzd-market-report")
    parser.add_argument("--topic", "-t", required=True)
    parser.add_argument("--keywords", "-k", nargs="+", help="Search keywords for signal collection")
    parser.add_argument("--audience", default="B2B Cross-Border Business Leads")
    parser.add_argument("--window", type=int, default=30, help="Window days (default 30)")
    parser.add_argument("--method", default="auto", choices=["auto", "brave", "ddgs"])
    parser.add_argument("--from-research", help="Path to hlzd-b2b-research JSON output (overrides signal collection)")
    parser.add_argument("--output-html", "-H", help="Write HTML report to this path")
    parser.add_argument("--output-md", "-M", help="Write Markdown report to this path")
    args = parser.parse_args()

    b2b_input = None
    if args.from_research:
        b2b_input = json.loads(Path(args.from_research).read_text(encoding="utf-8"))

    report = run(
        topic=args.topic,
        keywords=args.keywords,
        audience=args.audience,
        window_days=args.window,
        output_html=args.output_html,
        output_md=args.output_md,
        collect_method=args.method,
        b2b_research_input=b2b_input,
    )

    print(json.dumps({"topic": args.topic, "sections": list(report.keys()),
                       "html_bytes": len(args.output_html and Path(args.output_html).read_text(encoding="utf-8") or ""),
                       "md_bytes": len(args.output_md and Path(args.output_md).read_text(encoding="utf-8") or "")},
                      ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
