---
name: hlzd-trade-compliance
description: "B2B 工业品贸易合规护栏 —— 4 + 1 道检查 (OFAC SDN / EU Consolidated / BIS Entity List / Country-Based Embargo + ECCN 双用途粗筛)，输出 3 态 clearance (CLEARED / PENDING_REVIEW / BLOCKED) + 完整 audit_trail + Markdown 报告。Use when 用户说'合规'、'OFAC 制裁'、'出口管制'、'SDN 检索'、'贸易合规'、'sanctions screen'、'dual-use check'、'export compliance'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: trade-compliance
  triggered_by:
    - 合规
    - OFAC 制裁
    - 出口管制
    - SDN 检索
    - 贸易合规
    - 双用途
    - sanctions screen
    - dual-use check
    - export compliance
    - ECCN
---

# HLZD Trade Compliance

5 道检查 (4 buyer-side + 1 product-side) + 三态路由，挡住 V0.1 已知的常见制裁实体 / 禁运国家 / 双用途品类。

---

## When to use

调用本 Skill 当用户：

- **每次收海外询盘** —— 一票询盘进来，先跑 compliance，再决定报价 / 屏蔽
- 任何"B 类"以上客户的新询盘 —— 不让 Hezbollah 命中 → 你填了 DHL 单子被海关扣货
- 任何产品涉及 ECCN（加密 / 高端材料 / 化学武器前体）
- 内部合规审计：每月底跑一次全量 buyer/country 抽查

**不要调用本 Skill 当**：

- 询盘评级 D（已经在 `hlzd-inquiry-qualify` 拦截）
- 卖家是您的复购客户（已知合规过）
- 法规授权：通过商务部 / 银行 / 律所做正式验证（v0.1 是粗筛，绝对不是法律意见）

---

## How this skill is invoked

```bash
# 1. 准备 transaction JSON
cat << 'EOF' > tx.json
{
  "buyer_name": "Aramco Trading Co.",
  "buyer_country": "Saudi Arabia",
  "product": "OCTG casing",
  "hs_code": "730429",
  "end_use_country": "Saudi Arabia",
  "incoterm": "CIF",
  "value_usd": 850000
}
EOF

# 2. 跑合规检查
py scripts/cli.py --input tx.json --pretty

# 3. 生成 Markdown 报告
py scripts/render_report.py < report.json > report.md
```

输出结构：

```json
{
  "clearance": "CLEARED" | "PENDING_REVIEW" | "BLOCKED",
  "final_action": "Proceed with documentation; periodic re-check required.",
  "rationale": "...",
  "check_results": [...],
  "audit_trail": [...],
  "data_versions": {...},
  "data_source_attribution": [...]
}
```

`cli.py` 的 exit code 也作为机器可读的信号：`0 = CLEARED` / `1 = PENDING_REVIEW` / `2 = BLOCKED`，方便 CI 拦截。

---

## 5 道检查

| # | Check | Source | What it does | Default severity |
|---|---|---|---|---|
| 1 | `ofac_sdn_name_match` | `data/ofac_sdn.csv` (33 entries) | OFAC Specially Designated Nationals 实体的模糊匹配 | BLOCK |
| 2 | `eu_consolidated_name_match` | `data/eu_consolidated.csv` (17 entries) | EU Council Consolidated List (CFSP Decisions) | BLOCK |
| 3 | `bis_entity_name_match` | `data/bis_entity.csv` (15 entries) | BIS Entity List / Denied Persons List | REVIEW |
| 4 | `country_embargo_match` | `lib.COUNTRY_EMBARGOES` (12 countries) | Country-Based Sanctions (Iran / NK / Syria / Cuba / Crimea / Donetsk / Luhansk / Venezuela / Belarus / Russia / Myanmar / Zimbabwe) | BLOCK or REVIEW |
| 5 | `eccn_dual_use_keyword` | `lib.DUAL_USE_KEYWORDS` (15 keywords) + `eccn_map` (HS→ECCN) | 双用途商品粗筛 (加密 / 高端材料 / UAV / 化学武器前体) | REVIEW |

每条 check 都生成一条 `audit_trail` entry（timestamp + version + matched + flags_count），便于合规审计。

### v0.1 vs production

| v0.1 (现在) | v0.2 (target) |
|---|---|
| 33 OFAC SDN 静态子集 | 完整 SDN_ENHANCED (1.5 万行) via Treasury API |
| 17 EU Consolidated 静态子集 | 完整 EU FSF via CFSP RSS feed |
| 15 BIS Entity List 静态子集 | 完整 BIS via commerce.gov CSV |
| 12 Country Embargo 综合 OFAC + EU | 接 OFAC + EU 双独立 feed |
| 15 dual-use 关键词 | 接 BIS Commerce Control List ECCN 编码库 |

---

## Clearance 三态路由

```
                        all_flags 有一 BLOCK?
                       /               \
                yes /                 \ no
                   /                   \
              BLOCKED                  all_flags 有一 REVIEW?
       "DO NOT ship,                  /               \
        escalate to officer"     yes /                 \ no
                                      /                   \
                                PENDING_REVIEW           CLEARED
                          "HOLD + legal review"   "Proceed with documentation"
```

代码：`scripts/check.py:run_compliance_check` 内 `if any(f.severity == "BLOCK") ... elif REVIEW ... else CLEARED`。

---

## Output schema

### Top-level

```json
{
  "$schema": "hlzd/trade-compliance/v1",
  "product": "OCTG casing",
  "hs_code": "730429",
  "buyer_name": "Aramco Trading Co.",
  "buyer_country": "Saudi Arabia",
  "end_use_country": "Iran",
  "incoterm": "CIF",
  "timestamp_utc": "2026-07-15T03:43:00Z",
  "clearance": "BLOCKED",
  "final_action": "DO NOT ship; US/EU/UN sanctions apply.",
  "rationale": "At least one BLOCK-level finding.",
  "check_results": [...],
  "audit_trail": [
    { "check": "ofac_sdn_name_match", "data_version": "static_2026_q3",
      "matched": true, "flags_count": 1, "timestamp_utc": "..." },
    ...
  ],
  "data_versions": {
    "ofac_sdn_name_match": "static_2026_q3",
    ...
  },
  "data_source_attribution": ["ofac_sdn_name_match:static_2026_q3", ...]
}
```

### Check result schema

每个 `check_results[]` 元素：

```json
{
  "check_name": "ofac_sdn_name_match",
  "source_version": "static_2026_q3",
  "matched": true,
  "flags": [
    {
      "rule_id": "OFAC-SDN-SDGT",
      "severity": "BLOCK",
      "source": "ofac_sdn",
      "evidence": "Hezbollah",
      "rationale": "Buyer name fuzzy-matches OFAC SDN entry (program: SDGT).",
      "recommended_action": "HALT + escalate to compliance officer + transaction freeze."
    }
  ],
  "metadata": { "rows_loaded": 33, "matches": [...] }
}
```

---

## Fuzzy matching algorithm

`O(n)` 简单匹配 — 每个候选 CSV 行做 4 级：

1. **Exact normalized** (`normalize_name` 后完整相等)
2. **Bidirectional substring** (任一方含另一方 ≥ 6 chars)
3. **Token-level share** (共享 token 中有 ≥ 1 个 ≥ 6 chars, e.g. "Huawei")
4. **Stopword-filtered** (去除 `industrial` / `group` / `company` 等泛词避免误命中)

例：
- "Hezbollah Procurement" 匹配 OFAC SDN → "Hezbollah"（exact）→ BLOCK
- "Wagner Military Group" 匹配 OFAC SDN → "Wagner Group"（substring）→ BLOCK
- "Huawei Procurement LLC" 匹配 OFAC + EU + BIS → "Huawei Technologies"（token）→ BLOCK
- "ACME Industrial Imports" 不应命中 "Iran Aircraft Manufacturing Industrial Co"（industrial 被 stopword 过滤）→ clean

---

## Sample integration

### 嵌入 `hlzd-inquiry-qualify` (从 5 维评分升级)

把 `inquiry-qualify` 的合规粗筛替换/补充为正式 `hlzd-trade-compliance`：

```python
# 在 inquiry-qualify 的 evaluation step 加
import trade_compliance

tx = {"buyer_name": parsed_customer.company_name,
       "buyer_country": parsed_customer.country,
       "product": parsed_product.name,
       "hs_code": parsed_product.hs_code,
       "incoterm": parsed_inquiry.incoterm}

compliance_report = trade_compliance.run_compliance_check(tx)
if compliance_report.clearance == "BLOCKED":
    return "halt_to_compliance_officer"
elif compliance_report.clearance == "PENDING_REVIEW":
    return "review_required"
```

### 嵌入 `hlzd-customer-due-diligence` (替换 OFAC 静态子集)

`diligence` 当前的 OFAC 用 20 条静态，**应替换为合规 Skill**：

```python
# diligence 的 evaluate_buyer 加：合规检查
from hlzd_trade_compliance import run_compliance_check

tx = {"buyer_name": buyer["importer_name"], ...}
cr = run_compliance_check(tx)
if cr.clearance == "BLOCKED":
    return halt_result  # 比 5 维评分更暴力
```

（v0.1 已留接口，v0.2 替换。）

---

## Anti-pattern / Limitations

| 限制 | 处置 |
|---|---|
| 静态 CSV 仅 80 行 | v0.2 接 OFAC/EU/BIS 实时 API |
| Fuzzy match 可能误判 (e.g. shared "Industrial" 单词) | 已用 stopword 过滤；建议复核 BLOCKED 后再用人工致电 buyer |
| v0.1 不审计 OFAC 50% Rule | 提醒客户 ship to 3rd country 时 50% 规则可能触发 |
| 没有「de minimis exception」检查 | 比特币 / 灰关品类需手工 |
| 不报 EAR99 vs ECCN 分类本身 | ECCN 分类是律师工作 |

---

## Related Skills

```
hlzd-inquiry-qualify        (合规粗筛升级)
        |
        v
★ hlzd-trade-compliance ★ ← 本 Skill - 完整 5 道检查
        |
        v
hlzd-customer-due-diligence  (应为下游 — 替换 OFAC 静态子集)
hlzd-cold-outreach           (CLEARED 后才允许发邮件)
```

**前置**：客户的 buyer name + country + product + HS code
**后继**：CLEARED → 报价 + 发邮件；PENDING_REVIEW → 法务 review；BLOCKED → 整票冻结

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：5 道检查 + 三态路由 + 80 行静态 CSV |

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
