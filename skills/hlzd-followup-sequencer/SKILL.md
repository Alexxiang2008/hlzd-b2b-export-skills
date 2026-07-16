---
name: hlzd-followup-sequencer
description: "B2B 邮件跟进序列生成 —— 输入 cold-outreach 输出 + sent_at 时间戳，按 Day 7 / 14 / 21 自动判定阶段输出跟进邮件草稿（en / es 双语）。Use when 用户说'邮件跟进'、'Day 7 提醒'、'客户没回'、'需要催一下'、'follow up'、'day 14'、'cold email reminder'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: follow-up
  triggered_by:
    - 邮件跟进
    - Day 7 提醒
    - 客户没回
    - 需要催一下
    - follow up
    - cold email reminder
    - day 14
    - day 21
---

# HLZD Follow-up Sequencer

把"上次发件后第 N 天"自动转成"该发什么跟进邮件"。

## 阶段

| 距发件天数 | 阶段 | 动作 |
|---|---|---|
| 0-6 | `pending` | 不动 |
| 7-13 | `day_7_nudge` | 短提醒 — "上周一封信您看到了吗" |
| 14-20 | `day_14_followup` | 加 value + 主动约 call |
| ≥ 21 | `day_21_breakup` | 关闭循环 — "下季度再联系" |

## 用法

```bash
# 接 cold-outreach 输出
py scripts/cli.py --input outreach.json --output followups.json

# 测试场景 (override now date)
py scripts/cli.py --input outreach.json --as-of 2026-07-15
```

## Output schema

```json
{
  "$schema": "hlzd/followup-sequencer/v1",
  "report_date_utc": "2026-07-16T07:00:00Z",
  "summary": {
    "total_emails": 5,
    "actions_due": 3,
    "by_stage": {"day_7_nudge": 1, "day_14_followup": 1, "day_21_breakup": 1},
    "pending": 2,
    "errors": 0
  },
  "actions": [
    {
      "buyer": "Aramco Trading Co.",
      "contact": "Mr. Ahmed",
      "country": "SA",
      "stage": "day_7_nudge",
      "days_since_sent": 8,
      "subject": "Re: OCTG casing for Saudi",
      "body": "Hi Mr. Ahmed, ..."
    }
  ]
}
```

CLI exit code: 0 if no actions, 1 if actions due (cron-friendly).

## Related Skills

- `hlzd-cold-outreach` (上游) — 提供 input emails 列表
- `hlzd-customer-due-diligence` (相关) — 跟进前再 verify 买家是否仍合规
- `hlzd-pipeline-viz` (下游) — 累计 follow-up 转化率

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：Day 7 / 14 / 21 + en / es 双语 |
