#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hlzd-daily-report lib 测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import (  # noqa: E402
    validate_daily_report, summarize_day, morning_briefing_template,
    activity_heatmap,
)


SAMPLE_REPORT = {
    "date": "2026-07-16",
    "user_id": "u-001",
    "rfqs_handled": 10,
    "rfqs_quoted": 6,
    "meetings": 3,
    "followups_sent": 8,
    "revenue_usd": 75000,
    "tomorrow_plan": ["跟进 Aramco 报价", "准备 Italy 客户会议"],
}


def test_validate_complete():
    assert validate_daily_report(SAMPLE_REPORT) == []


def test_validate_missing_fields():
    incomplete = {"date": "2026-07-16"}
    missing = validate_daily_report(incomplete)
    assert "rfqs_handled" in missing
    assert "tomorrow_plan" in missing


def test_summarize_day():
    s = summarize_day(SAMPLE_REPORT)
    assert s["total_activity"] == 21   # 10 + 3 + 8
    assert s["conversion_rate"] == 0.6
    assert s["revenue_usd"] == 75000
    assert len(s["highlights"]) >= 2   # 报价>=5 + 营收>=50k


def test_morning_briefing_includes_plan():
    out = morning_briefing_template(SAMPLE_REPORT, ["跟进客户 X", "审 L/C 模板"])
    assert "今日计划" in out
    assert "1. 跟进客户 X" in out
    assert "2. 审 L/C 模板" in out
    assert "Aramco" not in out  # tomorrow_plan 字段不进入输出，只渲染 today_plan


def test_activity_heatmap():
    blocks = ["09:00-10:00", "09:30-10:30", "14:00-15:00", "14:30-15:30"]
    h = activity_heatmap(blocks)
    assert h == {"09:00": 2, "14:00": 2}


def test_highlights_threshold_quotes():
    r = dict(SAMPLE_REPORT, rfqs_quoted=4, revenue_usd=1000, meetings=0)
    s = summarize_day(r)
    assert s["highlights"] == []  # 报价<5 + 营收<50k + 会议<3 → 无亮点
