---
name: hlzd-solution-match
description: "B2B 工业品询盘方案匹配 —— 输入询盘（产品 + 数量 + 认证 + 工况）+ 产品目录 → 输出 3 套方案（best_match / alternative / cost_effective）+ 5 维匹配评分 + 风险检查。Use when 用户说'方案推荐'、'推荐 3 套'、'选最合适的'、'客户要 NACE / sour service 该推什么 SKU'、'3 个备选方案'、'B2B solution recommendation'、'SKUs match'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: solution-matching
  triggered_by:
    - 方案推荐
    - 推荐3套
    - 备选方案
    - 选最合适
    - solution match
    - SKU match
    - match product to inquiry
---

# HLZD 方案匹配（Solution Match）

把"客户要什么" + "我能卖什么" → 3 套推荐：best_match / alternative / cost_effective。

---

## When to use

调用本 Skill 当用户：

- 拿到询盘（来自 `hlzd-inquiry-qualify` Grade A/B 输出的 enriched 询盘）
- 想给他 3 套选择（不是单 SKU）
- 想评分 vs 风险 vs 价格 三个维度看

**不要调用本 Skill 当**：

- 客户只要 1 个 SKU（直接卖就行）
- 还没拿到询盘（先用 inquiry-qualify）

---

## How this skill is invoked

```bash
# 1. 询盘（enquiry）JSON：含 product + quantity + certifications_required + lead_time_days + text
# 2. 产品目录（catalog）JSON：可选 — 默认用 lib.DEFAULT_CATALOG

cat << 'EOF' | py scripts/cli.py --stdin
{"product": "OCTG", "quantity": "500 tons", "certifications_required": ["API 5CT", "NACE MR0175"],
 "text": "sour service oilfield", "lead_time_days": 60}
EOF

# 或
py scripts/cli.py --input enquiry.json --catalog catalog.json --pretty
```

输出：

```json
{
  "$schema": "hlzd/solution-match/v1",
  "best_match":      { "sku": "...", "match_score": 96, "scoring_breakdown": {...}, "risks": [], "rationale": "..." },
  "alternative":     { "sku": "...", "match_score": 91, ... },
  "cost_effective":  { "sku": "...", "match_score": 80, ... },
  "all_risks":       ["missing_cert:rohs", "below_moq"]
}
```

---

## 5-维匹配评分

| 维度 | 满分 | 内容 |
|---|---|---|
| **D1 规格匹配** | 30 | 品类匹配 (8) + 认证匹配 (12) + 应用场景匹配 (10) |
| **D2 数量匹配** | 15 | 询盘数量 vs MOQ (8) + vs 月产能 (7) |
| **D3 交期匹配** | 20 | 客户期望 vs SKU 标准 lead_time |
| **D4 价格梯度** | 15 | tier 1 = 15; tier 0/2 = 10; 其他 = max(0, 15-abs(t-1)*8) |
| **D5 风险检查** | 20 | 干净 → 20; 每个 risk (-4) |

---

## 3 套方案生成策略

| 方案 | 选择规则 |
|---|---|
| **best_match** | 评分最高 + 风险最少 |
| **alternative** | 与 best 不同 tier 的次优 |
| **cost_effective** | top 3 中 tier 最小（最便宜）|

**特殊情况**：如果 catalog 只有 1 SKU，三方案都返回该 SKU（仍报告 3 种 tier label）。

---

## Output schema

```json
{
  "$schema": "hlzd/solution-match/v1",
  "enquiry_product": "OCTG",
  "evaluated_skus": 5,
  "best_match": {
    "tier": "best_match",
    "sku": "OCTG-L80-95-BTC-PREMIUM",
    "category": "OCTG",
    "specs": { "grade": "L80", "od_inch": 9.625, "connection": "BTC", "tier": "premium",
               "unit_price_per_ton": 1480, "lead_time_days": 30, "moq_tons": 30, ... },
    "match_score": 96,
    "scoring_breakdown": { "D1_spec": {"score": 30, "max": 30, "missing": []}, ... },
    "risks": [],
    "rationale": "Recommended based on highest match score with lowest risk."
  },
  "alternative": { ... },
  "cost_effective": { ... },
  "all_risks": [...]
}
```

---

## Anti-pattern / Limitations

- 默认 product catalog 是 5 SKU 的硬编码（OCTG 3 类 + Solar Panel + Steel Structure）。真实部署接 ERP / 库存 API
- 评分全是 heuristic — 复杂产品规格匹配（如多维度公差）v0.2 接 LLM
- `customer_type` 在 solution-match 不出现 — 那是 `hlzd-cold-outreach` 的事
- 客户报价梯度（D4）只考虑 catalog 的 tier_index — 没考虑客户敏感度

---

## Related Skills

```
┌────────────────────────────┐
│  hlzd-inquiry-qualify         │  ← 上游：5维询盘评分
└────────────┬─────────────────┘
             ▼
┌────────────────────────────┐
│ ★ hlzd-solution-match ★  │  ← 本 Skill
└────────────┬─────────────────┘
             ▼
┌────────────────────────────┐
│  hlzd-quotation-gen         │  ← 下游：3 套报价
└────────────────────────────┘
```

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：5 SKU hardcoded catalog + 5 维评分 + 3 套方案生成 |

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
