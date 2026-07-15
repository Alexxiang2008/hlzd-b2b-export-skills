---
name: hlzd-customer-due-diligence
description: "B2B 海外采购商背调 —— 5 维评分（D1 公司真实性 / D2 公司实力 / D3 客户类型 / D4 采购能力 / D5 风险评估）打出 A/B/C/D 等级，制裁粗筛（OFAC SDN + 制裁国家 + dual-use + 欺诈高危），自动路由到 hlzd-cold-outreach 或 hlzd-trade-compliance。Use when 用户说'买家背调'、'客户验证'、'客户真实性'、'尽调'、'OFAC 检查'、'buyer validation'、'customer due diligence'、'KYC'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: customer-validation
  triggered_by:
    - 买家背调
    - 客户验证
    - 客户真实性
    - 客户尽调
    - buyer validation
    - KYC
    - customer due diligence
    - OFAC check
---

# HLZD 客户背调（Customer Due Diligence）

把"客户真实吗 / 实力够吗 / 有没有制裁风险"3 个问题，5 维评分 + 合规护栏一次性回答。

---

## When to use

调用本 Skill 当用户：

- 拿到 `hlzd-buyer-finder` 的买家清单，想筛掉垃圾、留真买家
- 询盘进来但 `hlzd-inquiry-qualify` 给了 D 级 / 边缘，需要补查
- 想跑 KYC / OFAC 复核（避免对接 Hezbollah / Wagner / Iran 等）
- 想自动分配 lead 给不同 sales 或插入 nurture

**不要调用本 Skill 当**：

- 客户已在合作（v0.1 用于未合作前的早期筛查）
- 需要 verify 已签合同的客户信用额度 —— 这是供应链金融风控，不在 v0.1 范围内

---

## How this skill is invoked

```bash
# 输入：buyer-finder 输出 JSON
py scripts/cli.py --input buyers.json --output diligence.json --pretty

# stdin 模式
cat buyers.json | py scripts/cli.py --stdin
```

输出每 buyer 的：

```
{
  "company_score": 0-100,
  "company_grade": "A" / "B" / "C" / "D",
  "scoring": { "D1_real": {...}, "D2_size": {...}, ... },
  "compliance": { "violations": [...], "passed": bool, "fraud_terms_detected": [...] },
  "recommendation": { "action": "outreach_24h|outreach_48h|nurture|archive|halt",
                       "next_skill": "hlzd-cold-outreach|nurture-sequence|hlzd-trade-compliance", ... }
}
```

---

## 5-维评分细则

| 维度 | 满分 | 取分规则 |
|---|---|---|
| **D1 公司真实性** | 25 | name 5 + LinkedIn 8 + 邮箱 5 (free) / 12 (公司) |
| **D2 公司实力** | 25 | 员工数 10 + 营收 10 + 行业信号 5（snippet 命中） |
| **D3 客户类型** | 15 | Manufacturer / EPC / End User / OEM = 15；Distributor = 10；Trader = 5；Unknown = 0 |
| **D4 采购能力** | 20 | 历史进口 15 + 项目经验 5（tender / EPC 命中） |
| **D5 风险评估** | 15 | 干净 → 15；制裁 / 欺诈 / SDN 命中 → 0 |

阈值：

| 总分 | 等级 | SOP |
|---|---|---|
| 90-100 | A | `hlzd-cold-outreach` 24h 内 |
| 70-89 | B | `hlzd-cold-outreach` 48h 内，补 D3/D2 缺失 |
| 50-69 | C | 入 nurture pool，90 天后重评 |
| 0-49 | D | 自动模板回 + 归档 |

---

## 合规护栏（5 道关卡）

| # | 检测 | 数据源 |
|---|---|---|
| 1 | **制裁国家** | `lib.SANCTIONED_COUNTRIES`（静态 list：North Korea / Iran / Syria / Cuba / Crimea / Donetsk / Luhansk）|
| 2 | **OFAC SDN 实体** | `lib.OFAC_SDN_STATIC_NAMES`（v0.1 静态子集 20 条；正式版接 OFAC SDN API 24h 刷新）|
| 3 | **Dual-use 关键词** | `OCTG for re-export` / `dual-use` / `encryption` 等 7 词 |
| 4 | **欺诈高危** | `advance payment to personal` / `western union payment only` 等 6 词 |
| 5 | **风险维度** | 上面任一命中 → D5 = 0 |

任一命中 → `recommendation.action = halt` + `next_skill = hlzd-trade-compliance`。

---

## Output schema

```json
{
  "$schema": "hlzd/customer-due-diligence/v1",
  "evaluated": 3,
  "failed": 0,
  "halt_recommended": 1,
  "by_grade": {"A": 0, "B": 1, "C": 0, "D": 2},
  "results": [
    {
      "importer_name": "Saudi Aramco Trading Co",
      "country": "Saudi Arabia",
      "company_score": 85,
      "company_grade": "B",
      "scoring": {
        "D1_real": {"score": 25, "max": 25, "missing": []},
        "D2_size": {"score": 15, "max": 25, "missing": ["revenue_indicator"]},
        "D3_type": {"score": 10, "max": 15, "missing": [], "customer_type": "Distributor"},
        "D4_procurement": {"score": 20, "max": 20, "missing": []},
        "D5_risk": {"score": 15, "max": 15, "missing": []},
        "total": 85,
        "grade": "B",
        "grade_reason": "Solid buyer. Outreach within 48h; supplement missing fields."
      },
      "compliance": {"violations": [], "passed": true, "fraud_terms_detected": []},
      "recommendation": {
        "action": "outreach_48h",
        "next_skill": "hlzd-cold-outreach",
        "priority": "P2",
        "rationale": "Grade B: solid buyer, supplement missing fields then outreach."
      }
    }
  ],
  "errors": []
}
```

---

## Sample integration

```bash
# 1. 找买家（来自 buyer-finder）
py ../hlzd-buyer-finder/scripts/cli.py --product "OCTG casing" --country SA \
    --output-json buyers.json

# 2. 背调
py scripts/cli.py --input buyers.json --output-json diligence.json --pretty

# 3. 自动 outreach（按 grade A/B 调 cold-outreach）
py ../hlzd-cold-outreach/scripts/cli.py --input diligence.json \
    --product "OCTG casing" --output-json outreach.json
```

3 步闭环完成：**调研 → 买家 → 背调 → 邮件**。

---

## Anti-patterns / Limitations

| 限制 | 处置 |
|---|---|
| OFAC SDN 列表是静态子集（20 条）| 正式版接 OFAC / EU / UN 公开 API，每 24h 同步 |
| LinkedIn 抽取仅 URL，正文验证需 v0.2 接 LLM |  |
| 公司规模 / 营收靠 snippet 关键词启发式 | 若只有 LinkedIn 主页，正文获取可补 LLM |
| `customer_type` 字段 buyer-finder v0.1 不输出 | v0.2 加；v0.1 用 `default_customer_type` 占位 |
| 不输出制裁国家 / 制裁实体的 source URL | 建议接 OFAC API 后带 URL（v0.2）|

---

## Related Skills

```
       ┌─────────────────────────┐
       │  hlzd-buyer-finder       │  ← 上游：买家列表
       └────────────┬────────────┘
                    │
                    ▼
       ┌─────────────────────────┐
       │ ★ hlzd-customer-due-    ★ │  ← 本 Skill
       │    diligence              │
       └────────────┬────────────┘
                    │
            ┌───────┼────────┐
            ▼       ▼        ▼
       outreach trade-      manual
       24/48h   compliance   review
       (合规过) (合规拦截)
```

**前置**：`hlzd-buyer-finder` 提供 buyer 输入
**后继**：`hlzd-cold-outreach`（合规过）或 `hlzd-trade-compliance`（拦截）

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：5 维评分 + OFAC SDN 静态子集 + dual-use + fraud + LinkedIn/website 抽取 |

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
