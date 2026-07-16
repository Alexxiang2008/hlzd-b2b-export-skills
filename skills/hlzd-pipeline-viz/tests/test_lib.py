"""Unit tests for hlzd-pipeline-viz."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lib  # noqa: E402


# ================================================================
# _deep_find
# ================================================================

class TestDeepFind:
    def test_top_level(self):
        assert lib._deep_find({"a": 1}, "a") == 1

    def test_nested(self):
        d = {"a": {"b": {"c": 42}}}
        assert lib._deep_find(d, "c") == 42

    def test_list_in_dict(self):
        d = {"items": [{"name": "x"}, {"name": "y"}]}
        names = lib._deep_find(d, "name")
        # First match
        assert names == "x"

    def test_missing(self):
        assert lib._deep_find({"a": 1}, "b") is None


# ================================================================
# aggregate_traces
# ================================================================

def _step1_inquiry_grade(grade: str, total: int) -> dict:
    return {
        "stage": "step_1",
        "matched": True,
        "company_grade": grade,  # flat key consumed by aggregate
        "scoring": {"grade": grade, "total": total},
    }


def _step3_diligence(grade: str, halt: int = 0, clearance: str = "CLEARED") -> dict:
    return {
        "stage": "step_3",
        "matched": True,
        "halt_recommended": halt,
        "clearance": clearance,
        "company_grade": grade,  # flat key consumed by aggregate
        "scoring": {"company_grade": grade, "total": 80},
    }


def _step6_quote(fob_usd: float = 100000.0, margin: float = 0.18) -> dict:
    return {
        "stage": "step_6",
        "incoterms": {"FOB": {"total_usd": fob_usd}},
        "profit_realized": {"ratio": margin},
    }


def _step7_negotiation(decision: str) -> dict:
    return {"stage": "step_7", "decision": {"decision": decision}}


class TestAggregate:
    def test_empty(self):
        agg = lib.aggregate_traces([])
        assert agg["traces_consumed"] == 0
        assert agg["stages_total"] == {}

    def test_basic_counters(self):
        trace = {"scenario_id": "test", "stages": {
            "step_1": _step1_inquiry_grade("B", 85),
            "step_3": _step3_diligence("B"),
            "step_6": _step6_quote(),
            "step_7": _step7_negotiation("accept_round_2"),
        }}
        agg = lib.aggregate_traces([trace])
        assert agg["traces_consumed"] == 1
        assert agg["stages_total"]["step_1"] == 1
        assert agg["grades"]["B"] == 2  # once from step_1 + once from step_3
        assert agg["clearance"]["CLEARED"] == 1
        assert agg["negotiation_decisions"]["accept_round_2"] == 1

    def test_halt_counted(self):
        trace = {"stages": {
            "step_3": _step3_diligence("D", halt=1, clearance="BLOCKED"),
        }}
        agg = lib.aggregate_traces([trace])
        assert agg["halted_count"] == 1

    def test_quote_total(self):
        trace = {"stages": {
            "step_6": _step6_quote(fob_usd=50000.0, margin=0.20),
        }}
        agg = lib.aggregate_traces([trace])
        assert agg["quote_total_usd"] == 50000.0
        assert agg["avg_margin"] == 0.20

    def test_margin_no_quote(self):
        agg = lib.aggregate_traces([])
        assert agg["avg_margin"] == 0.0

    def test_multiple_traces(self):
        traces = [
            {"scenario_id": "a", "stages": {"step_3": _step3_diligence("A")}},
            {"scenario_id": "b", "stages": {"step_3": _step3_diligence("B")}},
            {"scenario_id": "c", "stages": {"step_3": _step3_diligence("A")}},
        ]
        agg = lib.aggregate_traces(traces)
        assert agg["traces_consumed"] == 3
        assert agg["grades"]["A"] == 2
        assert agg["grades"]["B"] == 1

    def test_scenario_id_tracking(self):
        trace = {"scenario_id": "saudi-rfq", "stages": {
            "step_3": _step3_diligence("B", clearance="BLOCKED"),
        }}
        agg = lib.aggregate_traces([trace])
        assert "saudi-rfq" in agg["halted_scenario_ids"]


# ================================================================
# SVG renderers
# ================================================================

class TestFunnelSvg:
    def test_empty(self):
        svg = lib.render_funnel_svg({})
        assert "no data" in svg

    def test_single_stage(self):
        svg = lib.render_funnel_svg({"step_1": 5})
        assert "step_1" in svg
        assert "5" in svg

    def test_multiple_stages(self):
        svg = lib.render_funnel_svg({"step_1": 10, "step_2": 5, "step_3": 2})
        # 3 rect elements
        assert svg.count("<rect") == 3


class TestBarChartSvg:
    def test_empty(self):
        assert "no data" in lib.render_bar_chart_svg({})

    def test_data(self):
        svg = lib.render_bar_chart_svg({"A": 5, "B": 3})
        assert "A" in svg and "B" in svg
        assert "5" in svg and "3" in svg


# ================================================================
# render_dashboard
# ================================================================

class TestRenderDashboard:
    def test_returns_html(self):
        agg = lib.aggregate_traces([])
        html = lib.render_dashboard(agg, title="Test")
        assert html.startswith("<!DOCTYPE html>")
        assert "Test" in html
        assert "hlzd-pipeline-viz" in html

    def test_includes_kpis(self):
        agg = lib.aggregate_traces([])
        html = lib.render_dashboard(agg, title="X")
        for kpi in ("Traces", "Halts", "Follow-up actions due",
                     "Buyers evaluated", "Quote total",
                     "Avg margin", "Knowledge entities", "Graph nodes/edges"):
            assert kpi in html, f"missing KPI: {kpi}"

    def test_includes_charts(self):
        agg = lib.aggregate_traces([{"stages": {"step_1": _step1_inquiry_grade("A", 90)}}])
        html = lib.render_dashboard(agg, title="X")
        assert "<svg" in html
        assert "Pipeline Funnel" in html
        assert "Grade Distribution" in html
        assert "Negotiation Decisions" in html

    def test_includes_warn_when_halted(self):
        trace = {"stages": {"step_3": _step3_diligence("D", halt=1, clearance="BLOCKED")}}
        agg = lib.aggregate_traces([trace])
        html = lib.render_dashboard(agg, title="X")
        assert "warn" in html  # class="warn"
        assert "halt(s) detected" in html

    def test_includes_scenarios_table(self):
        trace = {"scenario_id": "saudi-rfq", "stages": {"step_1": _step1_inquiry_grade("B", 85)}}
        agg = lib.aggregate_traces([trace])
        html = lib.render_dashboard(agg, title="X")
        assert "saudi-rfq" in html
        assert "<table>" in html


# ================================================================
# run_pipeline
# ================================================================

class TestRunPipeline:
    def test_returns_keys(self):
        trace = {"stages": {"step_1": _step1_inquiry_grade("A", 90)}}
        result = lib.run_pipeline([trace], title="X")
        assert "$schema" in result
        assert "aggregation" in result
        assert "html_dashboard" in result
        assert "html_length" in result

    def test_html_length_matches(self):
        result = lib.run_pipeline([], title="X")
        assert result["html_length"] == len(result["html_dashboard"])

    def test_type_error_on_non_list(self):
        with pytest.raises(TypeError):
            lib.run_pipeline("not a list")
