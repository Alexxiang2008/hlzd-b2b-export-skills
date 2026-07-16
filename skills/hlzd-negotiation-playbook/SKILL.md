---
name: hlzd-negotiation-playbook
description: "B2B 报价让步推演 —— 输入初始报价 + 客户出价 + 红线（min_price / max_lead / min_advance），输出 3 轮价格 / 交期 / 账期让步轨迹 + 红线 hit 告警 + 决胜建议（accept_round_2 / counter / counter_with_freight / walk_away / accept_round_3）。Use when 用户说'让步'、'谈判'、'压价'、'让步轨迹'、'客户出价太低'、'walk-away 还是接'、'round 1/2/3 让步'、'negotiation'、'concession path'、'counter offer'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: negotiation
  triggered_by:
    - 让步
    - 谈判
    - 压价
    - 让步轨迹
    - walk-away
    - counter offer
    - 客户出价太低
    - negotiation
    - concession path
---

# HLZD 谈判让步推演（Negotiation Playbook）

客户出价后，3 轮价格 / 交期 / 账期三维独立让步；最后一键给决策建议。

---

## When to use

调用本 Skill 当用户：

- 已经报价（`hlzd-quotation-gen` 输出），客户回了 counter-offer
- 想知道"再让多少合理 / 不能让到哪条线 / 应该 walk-away 吗"
- 想看到 3 轮的逐轮让步轨迹，而非一次性"是 / 否"

**不要调用本 Skill 当**：

- 还没报价（先走 `hlzd-quotation-gen`）
- 客户已签合同（这时候走 `hlzd-after-sales` —— v0.2 计划）
- 单纯问"该报什么价"（应该用 `hlzd-quotation-gen`）

---

## How this skill is invoked

```bash
# 输入：
# 1. quote.json (hlzd-quotation-gen 输出)
# 2. customer_response 文本或 JSON

py scripts/cli.py \
    --quote quote.json \
    --response "We can pay USD 1300 per ton, 30% advance" \
    --redline-price 1300 \
    --pretty
```

或：

```bash
echo '{"target_price": 1300, "desired_lead_days": 30, "advance_pct": 30}' > response.json
py scripts/cli.py --quote quote.json --response response.json --pretty
```

---

## 算法：3 轮 × 3 维

### 价格（默认 5% / 3% / 2% 累计 10%）

```
Round 1: 让 5% off  initial
Round 2: 让 3% additional
Round 3: 让 2% additional  → 总让 10%
```

任何 round 后 `proposed_price < target_price`（客户出价）= "我们让穿了 target" = 红线 hit → 不应继续让步。

### 交期（默认 0 / 5 / 10 天）

```
Round 1: 让 0 天
Round 2: 让 5 天
Round 3: 让 10 天  → 总让 15 天
```

公式：`new_lead = initial - cum`，但 `min(new_lead, desired_lead)`。Round 3 后 `initial - cum > desired` 表示仍然达不到客户需求 → 红线。

### 账期（默认 30/70 → 20/80 → 10/90）

让 advance 占比下降、balance 占比上升。每次让 10pp。

---

## Decision matrix

| 价格 breach | 交期 breach | 模式 | 动作 |
|---|---|---|---|
| — | — | 默认 | `accept_round_2`（前两轮就锁定，第三轮 Reserve） |
| ✓ | — | `counter` | 建议重新 tier（换 economic SKU）或砍 scope |
| — | ✓ | `counter_with_freight` | 部分 air freight（买家付溢价）|
| ✓ | ✓ | `walk_away` | 红线全破，转 senior 决策 |
| — | — | `--competitor-risk` flag | `accept_round_3`（快接防丢单）|

---

## Output schema

```json
{
  "$schema": "hlzd/negotiation-playbook/v1",
  "initial_state": {
    "price_initial_usd_per_ton": 1500,
    "lead_days_initial": 40,
    "advance_pct_initial": 30,
    "target_price_usd_per_ton": 1300
  },
  "redlines": {
    "price_floor_usd_per_ton": 1300,
    "max_lead_days": 30,
    "min_advance_pct": 10
  },
  "rounds": {
    "price": [
      {"round": 1, "concession_pct": 0.05, "cumulative_concession_pct": 0.05,
       "proposed_price_usd": 1425.0, "delta_from_initial_usd": -75.0,
       "delta_from_target_usd": 125.0, "breaches_redline": false},
      {"round": 2, "concession_pct": 0.03, "cumulative_concession_pct": 0.08, "proposed_price_usd": 1380.0, "..."},
      {"round": 3, "concession_pct": 0.02, "cumulative_concession_pct": 0.10, "proposed_price_usd": 1350.0, "..."}
    ],
    "lead_time": [
      {"round": 1, "concession_days": 0, "new_lead_days": 40, "breaches_redline": true},
      {"round": 2, "concession_days": 5, "new_lead_days": 35, "breaches_redline": true},
      {"round": 3, "concession_days": 10, "new_lead_days": 30, "breaches_redline": false}
    ],
    "payment_terms": [
      {"round": 1, "advance_pct": 30, "balance_pct": 70, "delta_from_initial_pct": 0},
      {"round": 2, "advance_pct": 20, "balance_pct": 80, "delta_from_initial_pct": -10},
      {"round": 3, "advance_pct": 10, "balance_pct": 90, "delta_from_initial_pct": -20}
    ]
  },
  "red_line_breached": {
    "price": false,
    "lead_time": false
  },
  "decision": {
    "decision": "accept_round_2",
    "rationale": "Default path: two-round concession + lock. Round 3 reserved if renewal.",
    "next_step": "send round 2 quote + set payment terms per payment_rounds[1]"
  }
}
```

---

## Anti-pattern / Limitations

| 限制 | 处置 |
|---|---|
| 让步幅度是固定（5/3/2 %）| CLI 允许改 `--concessions` 列表 |
| 没考虑客户行业 / 项目紧迫度 / 季节性 | v0.2 加 LLM 推演层 |
| 高风险国家不直接走 walk-away — 只建议 | 上层 Agent 用 `recommendation.decision` 做最终 gate |
| 单 buyer 单轮推演，不存会话 | v0.2 加 session_id |

---

## Related Skills

```
★ hlzd-solution-match ★  →  SKU 选取
        │
        ▼
★ hlzd-quotation-gen ★  →  3 套报价
        │
        ▼
★ hlzd-negotiation-playbook ★  ← 本 Skill
        │
        ▼
人工 review + 邮件发送
```

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：3 轮 × 3 维让步 + 红线 + 决策路由 |

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
