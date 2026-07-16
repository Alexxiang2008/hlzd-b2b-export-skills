---
name: hlzd-quotation-gen
description: "B2B 工业品自动报价 —— 输入 SKU + 数量 + 目的港 + 贸易术语（FOB / CIF / DDP），输出 3 套报价（每套含明细拆解）+ 利润健康检查（HEALTHY / LOW / HIGH / BELOW）+ 账期建议（30% advance / LC 等）。Use when 用户说'出报价'、'算价'、'报价单'、'清关价值'、'FOB 单价'、'CIF 报价'、'DDP 报价'、'自动报价'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: quotation
  triggered_by:
    - 出报价
    - 算价
    - 报价单
    - 清关价值
    - FOB单价
    - CIF报价
    - DDP报价
    - quotation
    - generate quote
    - cost calculation
---

# HLZD 智能报价（Quotation Generator）

把"SKU + 数量 + 目的港 + 贸易术语"变成 3 套可签 FOB/CIF/DDP 报价 + 健康检查。

---

## When to use

调用本 Skill 当用户：

- 拿到 `hlzd-solution-match` 出的 plan（best_match / alternative / cost_effective）
- 客户发了 RFQ 需要 24h 内回报价
- 想对比 FOB/CIF/DDP 三套不同条款下的真实利润
- 想加账期建议（30/70 T/T、LC、信用风险国）

**不要调用本 Skill 当**：

- 已经签了合同（这时候是真实履约，不是报价）
- 客户已经接受了报价（走合同细节）
- 单次大批量订单需要手工 custom 谈判（这是 negotiation-playbook）

---

## How this skill is invoked

```bash
# 接 solution-match 最佳方案
cat solution.json | py ../hlzd-solution-match/scripts/cli.py --stdin > best_plan.json
py scripts/cli.py --sku-json '{"sku":"X","currency":"USD","unit_price_per_ton":1480}' \
    --quantity 500 --country SA --incoterm FOB --pretty

# 或独立 CLI（直接传 SKU dict）
echo '{"sku":"OCTG-L80","currency":"USD","unit_price_per_ton":1480}' \
    | py scripts/cli.py --stdin --quantity 500 --country AE --incoterm CIF
```

CLI 参数：

| Flag | Default | 说明 |
|---|---|---|
| `--quantity` | 必填 | 数量（ton） |
| `--country` | 必填 | 目的国（ae / sa / us / ng ...）|
| `--incoterm` | "FOB" | FOB / CIF / DDP 任选 |
| `--currency` | "USD" | 输出币种 |
| `--margin` | 0.18 | 利润率（0.18 = 18%）|
| `--containers` | 1 | 20GP 集装箱数 |

---

## Output schema（3 套报价）

```json
{
  "$schema": "hlzd/quotation-gen/v1",
  "sku": "OCTG-L80-95-BTC-PREMIUM",
  "quantity_tons": 500,
  "target_country": "SA",
  "currency": "USD",
  "profit_margin_assumed": 0.18,
  "components": {
    "factory_unit_price_usd": 1480.0,
    "factory_cost_usd": 740000.0,
    "packaging_cost_usd": 9000.0,
    "export_rebate_usd": 81400.0,
    "ocean_freight_usd": 1200.0,
    "insurance_usd": 2625.21,
    "target_duty_rate": 0.06,
    "target_duty_usd": 43597.51,
    "customs_clearance_fee_usd": 200
  },
  "incoterms": {
    "FOB": { "total_usd": 781800.0, "unit_price_usd_per_ton": 1563.6 },
    "CIF": { "total_usd": 785625.21, "unit_price_usd_per_ton": 1571.25 },
    "DDP": { "total_usd": 829422.72, "unit_price_usd_per_ton": 1658.85 }
  },
  "profit_realized": {
    "absolute_usd": 110200.0,
    "ratio": 0.1409,
    "health": "BELOW_HEALTHY (10-15%)",
    "warning": "Margin 14.1% below healthy floor (15%). Negotiate higher price next round."
  },
  "payment_terms": {
    "primary": "30% T/T advance + 70% T/T against B/L copy",
    "fallback": "Irrevocable L/C at sight",
    "risk_note": null
  }
}
```

---

## 健康区间

| 健康等级 | 区间 | 含义 |
|---|---|---|
| **HIGH (> 25%)** | ratio > 0.25 | 可能失去商机（客户会觉得贵）|
| **HEALTHY (15-25%)** | 0.15 ≤ ratio ≤ 0.25 | 健康推荐区间 |
| **BELOW_HEALTHY (10-15%)** | 0.10 ≤ ratio < 0.15 | 偏低，下轮要求加价 |
| **LOW (< 10%)** | ratio < 0.10 | 危险，亏损边缘 |

`warning` 字段明示建议动作（"Negotiate higher price next round." 等）。

---

## 账期建议逻辑

| 风险等级 | Primary | Fallback |
|---|---|---|
| **普通国家 + 健康利润** | 30% T/T advance + 70% T/T against B/L | LC at sight |
| **高风险国家**（Iran / North Korea / Syria / Iraq） | 100% T/T 预付 | Tier-1 银行 LC |
| **普通国家 + 薄利**（< 10%） | LC at sight | 30/70 T/T + LC 混合 |

高风险国集合（v0.1 保守静态列表）。

---

## Sample integration

```bash
# 1. Solution
py ../hlzd-solution-match/scripts/cli.py --input enquiry.json --output best.json

# 2. Quotation
UNIT=$(jq -r '.best_match.specs.unit_price_per_ton' best.json)
echo "{\"sku\":\"X\",\"currency\":\"USD\",\"unit_price_per_ton\":$UNIT}" > sku.json
py scripts/cli.py --input sku.json --quantity 500 --country SA --incoterm FOB --output quote.json
```

完整闭环：**询盘 → 方案 → 报价**。

---

## Anti-pattern / Limitations

| 限制 | 处置 |
|---|---|
| 汇率是 v0.1 stub（FX_RATES_USD 静态）| 正式版接 Open Exchange Rates / 国家外管局 |
| 海运费按区域估价（±20% 误差）| 正式版接货代 API |
| 关税一律 6%（实际按 HS / 国家浮动）| 真实数据库可接 |
| 出口退税一律 11%（实际 9/13% 分品类）| 升级拆解 |
| 包装按 USD 18/ton 估算 | 接 ERP 实际重量 |

---

## Related Skills

```
hlzd-solution-match (best/alt/cost-effective plan)
        │
        ▼
★ hlzd-quotation-gen ★  → 3 套报价 + 健康检查 + 账期
        │
        ▼
hlzd-negotiation-playbook (3 轮让步轨迹)
```

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：FOB/CIF/DDP 3 套；利润检查 4 档；账期建议（含高风险国）|

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
