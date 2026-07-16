---
name: hlzd-pipeline-viz
description: "B2B Skill 链路可视化 —— 消费各 Skill trace JSON，输出 8 KPI 仪表盘 + 漏斗图 + 评级分布 + 决策分布 + halt 警报 self-contained HTML（纯 stdlib + inline SVG，零依赖）。Use when 用户说'链路可视化'、'Pipeline 仪表盘'、'B2B 转化漏斗'、'Funnel Dashboard'、'pipeline metrics'、'trace aggregate'、'B2B analytics'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: analytics
  triggered_by:
    - 链路可视化
    - 仪表盘
    - 漏斗
    - funnel dashboard
    - pipeline metrics
    - trace aggregate
    - B2B analytics
---

# HLZD Pipeline Viz

把多个 Skill 的 trace JSON 累计成一份 self-contained HTML dashboard。

## 8 KPI 卡片

| KPI | 来源 |
|---|---|
| Traces | 输入 trace 数 |
| Halts | compliance/fraud 拦截数 |
| Follow-up actions due | followup-sequencer 输出 |
| Buyers evaluated | diligence 输出 |
| Quote total (USD) | quotation-gen 累计 |
| Avg margin | quotation-gen ratio |
| Knowledge entities | knowledge-graph 累计 |
| Graph nodes/edges | knowledge-graph 累计 |

## 4 图表

- Pipeline Funnel (按 stage 数量降序 SVG trapezoid)
- Grade Distribution (横向条形图 A/B/C/D)
- Clearance 分布 (CLEARED/PENDING_REVIEW/BLOCKED)
- Negotiation Decisions (accept_round_2 / counter / ...)

## 用法

```python
import json
import lib

traces = [json.loads(p) for p in ["trace1.json", "trace2.json"]]
result = lib.run_pipeline(traces, title="HLZD Pipeline")
html = result["html_dashboard"]
open("dashboard.html", "w").write(html)
```

## Output

- `result["html_dashboard"]` —— 直接浏览器打开
- `result["aggregation"]` —— 累计指标 JSON (for further processing)

## Related Skills

- 所有 18 个 Skill (上游) —— 提供 trace 输入
- 自身是 v1.3 的下游 — 完成后可以做执行控制台

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：8 KPI + 4 图表 + halt 警报 + SVG 自包含 |
