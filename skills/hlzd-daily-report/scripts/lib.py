#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hlzd-daily-report — 日报结构 schema + 时间块统计 + 早会总结模板。

v0.1.0 仅交付 Pydantic-free schema dict 校验 + 模板渲染；v0.2 接入 LangBot 事件流。
"""
from __future__ import annotations
from collections import Counter
from typing import Dict, List, Tuple


REQUIRED_FIELDS = (
    "date", "user_id", "rfqs_handled", "rfqs_quoted",
    "meetings", "followups_sent", "revenue_usd",
    "tomorrow_plan",
)


def validate_daily_report(report: Dict) -> List[str]:
    """校验日报结构是否齐全。返回缺失字段列表。"""
    return [f for f in REQUIRED_FIELDS if f not in report]


def summarize_day(report: Dict) -> Dict:
    """生成摘要（LLM 调用前的结构化部分）。"""
    return {
        "date": report.get("date"),
        "total_activity": (
            int(report.get("rfqs_handled", 0))
            + int(report.get("meetings", 0))
            + int(report.get("followups_sent", 0))
        ),
        "conversion_rate": round(
            int(report.get("rfqs_quoted", 0))
            / max(int(report.get("rfqs_handled", 0)), 1), 4
        ),
        "revenue_usd": int(report.get("revenue_usd", 0)),
        "highlights": _extract_highlights(report),
    }


def _extract_highlights(report: Dict) -> List[str]:
    h: List[str] = []
    if report.get("rfqs_quoted", 0) >= 5:
        h.append(f"今日完成 {report['rfqs_quoted']} 个报价，节奏良好")
    if report.get("meetings", 0) >= 3:
        h.append(f"今日 {report['meetings']} 场客户会议，覆盖度不错")
    if report.get("revenue_usd", 0) >= 50000:
        h.append(f"今日成交 ${report['revenue_usd']:,}")
    return h


def morning_briefing_template(prev_day: Dict, today_plan: List[str]) -> str:
    """早会总结模板（输入昨日日报 + 今日计划）。"""
    s = summarize_day(prev_day)
    plan_label = "今日计划"
    stats_label = "数据"
    meetings_label = "客户会议"
    NL = "\n"
    output_lines = [
        "📊 昨日（" + str(s['date']) + "）" + stats_label + "：",
        "  - 询盘处理：" + str(prev_day.get('rfqs_handled', 0))
            + " / 报价：" + str(prev_day.get('rfqs_quoted', 0)),
        "  - " + meetings_label + "：" + str(prev_day.get('meetings', 0))
            + " / 跟进：" + str(prev_day.get('followups_sent', 0)),
        "  - 转化率：" + format(s['conversion_rate'] * 100, '.1f') + "%",
        "  - 营收：$" + format(s['revenue_usd'], ',d'),
    ]
    if s["highlights"]:
        output_lines.append("✨ 亮点：")
        for h in s["highlights"]:
            output_lines.append("  - " + h)
    output_lines.append(NL + "🎯 " + plan_label + "：")
    for i, plan in enumerate(today_plan, 1):
        output_lines.append("  " + str(i) + ". " + plan)
    return NL.join(output_lines)


def activity_heatmap(time_blocks: List[str]) -> Dict[str, int]:
    """统计时间块分布（输入 ISO 时间块列表如 ['09:00-10:00', '14:00-15:00']）。"""
    hours = Counter()
    for blk in time_blocks:
        if "-" in blk:
            start = blk.split("-")[0].split(":")[0]
            hours[f"{start}:00"] += 1
    return dict(sorted(hours.items()))
