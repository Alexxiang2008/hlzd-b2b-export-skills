#!/usr/bin/env python3
"""hlzd-market-report 测试套件。

覆盖：
- lib.py: 7 LAWS + normalize + schema + html escape
- render_html.py: 9 节输出完整性 + escape + 注入安全
- render_markdown.py: 8 节输出 + escape
- pipeline.py: assemble + from_b2b_research + run

运行：
  cd skills/hlzd-market-report
  py -m pytest tests/ -v --cov=scripts --cov-report=term-missing
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402
import render_html  # noqa: E402
import render_markdown  # noqa: E402
import pipeline  # noqa: E402


# ================================================================
# 1. lib — Voice Contract LAWS
# ================================================================

class TestVoiceContract:
    def test_law_1_body_starts_with_marker(self):
        ok, _ = lib.check_law_1("What I learned: This market is heating up")
        assert ok

    def test_law_1_body_not_starting_with_marker(self):
        ok, msg = lib.check_law_1("This market is heating up")
        assert not ok
        assert "What I learned" in msg

    def test_law_2_em_dash_detected(self):
        ok, msg = lib.check_law_2("Heating — up")
        assert not ok
        assert "em-dash" in msg.lower()

    def test_law_2_en_dash_detected(self):
        ok, _ = lib.check_law_2("Heating – up")
        assert not ok

    def test_law_2_valid_text(self):
        ok, _ = lib.check_law_2("Heating - up")
        assert ok

    def test_law_4_trailing_sources_block(self):
        ok, _ = lib.check_law_4("Body\n\nSources:\n- link")
        assert not ok

    def test_law_4_clean(self):
        ok, _ = lib.check_law_4("Body without trailing sources")
        assert ok

    def test_validate_compound(self):
        violations = lib.validate_voice_contract(
            body_first_line="What I learned: ...",
            candidate_text="Heating - up",
            body_text="Body",
            has_source_url=True,
        )
        assert violations == []

    def test_normalize_dashes(self):
        out = lib.normalize_dashes("Heating — up – fast")
        assert "—" not in out and "–" not in out
        assert " - " in out

    def test_law_7_brand_assumption(self):
        violations = lib.validate_voice_contract(
            body_first_line="What I learned: ...",
            candidate_text="clean text",
            has_brand_assumption=True,
        )
        assert any(v.law_id == "LAW_7" for v in violations)


# ================================================================
# 2. lib — schema validation
# ================================================================

class TestSchema:
    def test_valid_full_report(self):
        report = {
            "cover": {"headline": "x", "tagline": "y", "kpis": [], "three_step_plan": []},
            "toc": [],
            "solution_overview": {"recap": "y", "conclusion_table": []},
            "three_signals": {"signals": []},
            "platform_deep_dive": {"platforms": []},
            "strategic_comparison": {"vendors": [], "attributes": []},
            "action_plan": {"actions": []},
            "methodology": {"five_step": [], "five_dim": [], "seven_limitations": []},
            "footer_sources": {"sources": []},
        }
        errs = lib.validate_schema(report)
        assert errs == []

    def test_missing_section(self):
        errs = lib.validate_schema({})
        # 9 sections missing
        section_errs = [e for e in errs if "missing section" in str(e)]
        assert len(section_errs) == 9

    def test_missing_key(self):
        report = {"cover": {"headline": "x"}}  # 缺 tagline / kpis / three_step_plan
        errs = lib.validate_schema(report)
        assert any("missing key" in str(e) for e in errs)

    def test_section_must_be_dict(self):
        report = {"cover": "not a dict"}
        errs = lib.validate_schema(report)
        assert any("must be dict" in str(e) for e in errs)


# ================================================================
# 3. lib — HTML escape
# ================================================================

class TestEscape:
    def test_esc_quotes(self):
        assert lib.esc('<script>alert("x")</script>') == (
            '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;'
        )

    def test_esc_none(self):
        assert lib.esc(None) == ""

    def test_esc_number(self):
        assert lib.esc(42) == "42"

    def test_url_href_invalid(self):
        assert lib.url_href("not a url") == "#"

    def test_url_href_valid(self):
        assert lib.url_href("https://example.com") == "https://example.com"

    def test_md_link_with_url(self):
        out = lib.md_link("Reddit", "https://reddit.com")
        assert out == "[Reddit](https://reddit.com)"

    def test_md_link_without_url(self):
        assert lib.md_link("Foo", "") == "Foo"


# ================================================================
# 4. render_html — section rendering
# ================================================================

def _minimal_report() -> dict:
    return {
        "$schema": "hlzd/market-report/v1",
        "meta": {"topic": "OCTG casing", "audience": "B2B Cross-Border Business Leads",
                  "window_days": 30, "language": "en"},
        "cover": {
            "headline": "OCTG casing - Cross-Border Scan",
            "tagline": "30-day scan for cross-border leads",
            "kpis": [
                {"label": "Window", "value": "30", "unit": "days"},
                {"label": "Signals", "value": "12", "unit": ""},
            ],
            "three_step_plan": [
                {"step": "Step 1", "action": "Action one"},
                {"step": "Step 2", "action": "Action two"},
            ],
        },
        "toc": [{"id": "x", "title": "X"}, {"id": "y", "title": "Y"}],
        "solution_overview": {
            "recap": "Twelve signals surface across markets.",
            "conclusion_table": [
                {"metric": "M1", "finding": "f1", "implication": "i1"},
            ],
        },
        "three_signals": {
            "signals": [
                {"title": "Saudi OCTG demand rising",
                 "user_pain_quote": "Buyers struggle to find L80 stock",
                 "root_cause": "Aramco tender cycles",
                 "market_implication": "Apply for Aramco vendor list",
                 "sources": [{"name": "Reddit", "url": "https://reddit.com/r/x"}]}
            ]
        },
        "platform_deep_dive": {
            "platforms": [
                {"name": "Reddit", "stat": "12 results",
                 "findings": [{"headline": "h1", "body": "b1", "source_name": "src1",
                                "source_url": "https://example.com/x"}]}
            ]
        },
        "strategic_comparison": {
            "vendors": [{"name": "V1", "coverage": "high"}, {"name": "V2", "coverage": "medium"}],
            "attributes": ["Coverage"],
        },
        "action_plan": {
            "actions": [
                {"title": "Run validation",
                 "options": ["opt1", "opt2"],
                 "risk": "low",
                 "execution": "Run pipeline weekly"},
            ]
        },
        "methodology": {
            "five_step": ["s1", "s2"],
            "five_dim": ["d1", "d2"],
            "seven_limitations": ["l1", "l2", "l3", "l4", "l5", "l6", "l7"],
        },
        "footer_sources": {
            "sources": [{"name": "src", "url": "https://example.com/s", "category": "Reddit"}]
        },
    }


class TestRenderHtml:
    def test_render_outputs_valid_html(self):
        html = render_html.render_html(_minimal_report())
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_render_includes_all_sections(self):
        html = render_html.render_html(_minimal_report())
        for marker in ["cover", "Table of Contents", "Solution Overview",
                        "3 Core Signals", "Platform Deep Dive",
                        "Strategic Comparison", "3-Step Action Plan",
                        "Methodology", "Sources"]:
            assert marker in html, f"missing section: {marker}"

    def test_render_escapes_user_input(self):
        report = _minimal_report()
        report["cover"]["headline"] = '<script>alert("xss")</script>'
        html = render_html.render_html(report)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_render_handles_empty_sections(self):
        report = _minimal_report()
        report["three_signals"]["signals"] = []
        html = render_html.render_html(report)
        # no signal cards but other sections present
        assert "Solution Overview" in html

    def test_render_handles_empty_plaforms(self):
        report = _minimal_report()
        report["platform_deep_dive"]["platforms"] = []
        html = render_html.render_html(report)
        assert "Platform Deep Dive" in html

    def test_render_includes_meta(self):
        html = render_html.render_html(_minimal_report())
        assert "OCTG casing" in html
        assert "HLZD" in html

    def test_render_uses_safe_url_fallback(self):
        report = _minimal_report()
        report["footer_sources"]["sources"] = [{"name": "no url", "url": "", "category": "X"}]
        html = render_html.render_html(report)
        # 安全: 空 URL 不应被注入
        assert 'href="#"' in html

    def test_css_is_self_contained(self):
        html = render_html.render_html(_minimal_report())
        # CSS 必须 inline (无 external file ref)
        assert "<style>" in html and "</style>" in html
        assert '<link rel="stylesheet"' not in html
        assert 'src="http' not in html or "googleapis" not in html  # no google fonts


class TestRenderMarkdown:
    def test_renders_all_sections(self):
        md = render_markdown.render_markdown(_minimal_report())
        for marker in ["OCTG casing - Cross-Border Scan",
                        "Table of Contents",
                        "1. Solution Overview", "2. 3 Core Signals",
                        "3. Platform Deep Dive", "4. Strategic Comparison",
                        "5. 3-Step Action Plan", "6. Methodology & Limitations",
                        "7. Sources"]:
            assert marker in md, f"missing section: {marker}"

    def test_uses_inline_md_links(self):
        md = render_markdown.render_markdown(_minimal_report())
        assert "[Reddit]" in md or "[src]" in md or "Reddit" in md

    def test_markdown_clean_for_dashes(self):
        md = render_markdown.render_markdown(_minimal_report())
        # LAW 2 - no em-dash
        assert "—" not in md
        assert "–" not in md

    def test_handles_empty(self):
        report = _minimal_report()
        report["three_signals"]["signals"] = []
        report["action_plan"]["actions"] = []
        md = render_markdown.render_markdown(report)
        assert "B2B Market Report" in md or md  # 不崩即可


# ================================================================
# 5. pipeline — assemble / from_b2b_research / run
# ================================================================

class TestAssembleReport:
    def test_minimal_assemble(self):
        r = pipeline.assemble_report(topic="T", signals=[])
        for section in lib.REQUIRED_SECTION_KEYS:
            assert section in r, f"missing {section}"

    def test_assemble_with_signals(self):
        sigs = [{"title": "T1", "snippet": "S1", "url": "https://x.com/1", "source": "Reddit"}]
        r = pipeline.assemble_report(topic="T", signals=sigs)
        # 3 signals 取前 3
        assert len(r["three_signals"]["signals"]) >= 1
        # sources 去重
        assert any(s.get("url") == "https://x.com/1" for s in r["footer_sources"]["sources"])

    def test_assemble_signals_dedup(self):
        sigs = [
            {"title": "T1", "snippet": "S1", "url": "https://a.com", "source": "Reddit"},
            {"title": "T2", "snippet": "S2", "url": "https://a.com", "source": "Reddit"},
            {"title": "T3", "snippet": "S3", "url": "https://b.com", "source": "DDGS"},
        ]
        r = pipeline.assemble_report(topic="T", signals=sigs)
        # URL 去重
        urls = [s["url"] for s in r["footer_sources"]["sources"]]
        assert len(urls) == len(set(urls))


class TestFromB2BResearch:
    def test_basic_transform(self):
        research = {
            "product": "OCTG",
            "markets": ["UAE", "Saudi"],
            "hs_code_used": "730429",
            "hs_code_candidates": [],
            "trade_data": {
                "UAE": {"hs_code": "730429", "reporter": "784", "total_import_value_usd": 5e8,
                         "data_source": "UN Comtrade",
                         "countries": [{"country": "China", "import_value_usd": 4e8, "share_pct": 80}]},
            },
            "trends": {}, "buyers": {}, "warnings": [],
        }
        r = pipeline.from_b2b_research(research)
        # sections 齐
        for s in lib.REQUIRED_SECTION_KEYS:
            assert s in r
        # headline 提到 OCTG
        assert "OCTG" in r["cover"]["headline"]
        # 1 market 落 1 signal
        assert len(r["three_signals"]["signals"]) >= 1


class TestRunPipeline:
    def test_run_returns_dict(self, tmp_path):
        html_out = tmp_path / "report.html"
        md_out = tmp_path / "report.md"
        r = pipeline.run(
            topic="Test topic",
            keywords=["test", "topic"],
            output_html=str(html_out),
            output_md=str(md_out),
            collect_method="ddgs",  # 假设未装 ddgs
        )
        assert isinstance(r, dict)
        assert html_out.exists() and html_out.stat().st_size > 1000
        assert md_out.exists() and md_out.stat().st_size > 100

    def test_run_with_b2b_research(self, tmp_path):
        research = {
            "product": "Test product",
            "markets": ["US"],
            "hs_code_used": "123456",
            "hs_code_candidates": [],
            "trade_data": {}, "trends": {}, "buyers": {}, "warnings": [],
        }
        html_out = tmp_path / "report.html"
        pipeline.run(
            topic="x",
            b2b_research_input=research,
            output_html=str(html_out),
        )
        assert html_out.exists()
        html = html_out.read_text(encoding="utf-8")
        assert "Test product" in html


# ================================================================
# 6. End-to-end schema validation
# ================================================================

class TestEndToEndSchema:
    def test_full_assemble_passes_schema(self):
        r = pipeline.assemble_report(
            topic="Topic X",
            signals=[{"title": "T", "snippet": "S", "url": "https://x.com", "source": "Reddit"}],
            vendors=[{"name": "V1", "coverage": "high"}],
            attributes=["Coverage"],
            actions=[{"title": "A", "options": [], "risk": "low", "execution": "E"}],
            sources=[{"name": "src", "url": "https://x.com", "category": "Reddit"}],
        )
        errs = lib.validate_schema(r)
        assert errs == [], f"schema errors: {errs}"

    def test_run_outputs_validate(self):
        r = pipeline.run(topic="X", keywords=["X"], collect_method="ddgs")
        errs = lib.validate_schema(r)
        assert errs == [], f"run produced invalid: {errs}"
