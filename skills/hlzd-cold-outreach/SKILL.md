---
name: hlzd-cold-outreach
description: "B2B 海外采购商触达邮件草稿生成 —— 5 类买家模板（Manufacturer / EPC / Distributor / OEM / End User / Trader）× 双语（en/es），每 buyer 自动选模板 + 替换变量 + 生成 Day 7 / Day 14 跟进序列。Use when 用户说'发邮件'、'写开发信'、'cold outreach'、'客户开发'、'邮件草稿'、'跟进序列'、'cold email draft'、'follow-up sequence'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: outreach
  triggered_by:
    - 发邮件
    - 写开发信
    - 客户开发
    - 邮件草稿
    - 跟进序列
    - cold outreach
    - cold email
    - follow-up sequence
    - vendor outreach
---

# HLZD Cold Outreach

把"已通过背调的买家名单 + 产品 context"批量变成可发的开发信 + 跟进序列。

---

## When to use

调用本 Skill 当用户：

- 拿到 `hlzd-customer-due-diligence` 的 grade A/B 买家清单
- 想批量生成邮件草稿（不是自动发）
- 想要 en + es 双语（西语国家覆盖拉美 / 西班牙 / 部分美国客户）
- 跟进 7/14 天未读 → 自动 day_7 / day_14 邮件

**不要调用本 Skill 当**：

- 想自动 send（v0.1 只生成草稿，不发）；发邮件请用 SendGrid / Mailgun 单独 Skill（v0.2 计划）
- 客户已在合作（v0.1 针对 cold outreach）
- 询盘评级 B+ 但已经在你的 CRM 跟进中

---

## How this skill is invoked

```bash
# 接 diligence 输出
py scripts/cli.py --input diligence.json \
    --product "OCTG casing" \
    --sender-company "HLZD" \
    --sender-name "Alex" \
    --output outreach.json --pretty

# 手动指定 buyer + product context
cat << 'EOF' | py scripts/cli.py --stdin --product "Solar Panel"
[{"importer_name": "Sun Co", "country": "US", "customer_type": "Distributor"}]
EOF
```

CLI 参数：

| Flag | Default | 说明 |
|---|---|---|
| `--product` | "industrial equipment" | 产品名/品类（自动填模板） |
| `--sender-company` | "HLZD" | 发件人公司 |
| `--sender-name` | "Sales Team" | 发件人名 |
| `--sender-email` | "sales@hlzd.example.com" | 发件邮箱（落到签名） |
| `--sender-phone` | "+86 138 0000 0000" | 发件电话 |
| `--default-language` | "en" | en / es |
| `--default-customer-type` | "Manufacturer" | 自动路由 fallback |
| `--no-followups` | False | 不生成 Day 7/14 跟进 |

---

## Template system

**6 类买家 × 2 种语言 = 12 个模板**：

| 客户类型 | 模板场景 |
|---|---|
| **Manufacturer** | 长期可靠供应商叙事，强调产能 + 认证 |
| **EPC** | 项目驱动，强调包装 + 文档 + 履约时间 |
| **Distributor** | 经销渠道扩张，MOQ + 价目梯度 + 区域保护 |
| **OEM** | 品牌代工，强调标签设计 + 批次 QC + 年度承诺 |
| **End User** | 直采省中间商，强调落地成本 + 15% 节省 |
| **Trader** | 快速报价，FOT 港口 + 价目 + 24h 回复 |

每模板含：subject / opening / value_prop / cta / signature 四段。

### 变量替换

模板里变量 `{{var}}` 来自 3 层 merge：
1. **Built-in defaults**（HLZD 营业默认值）
2. **product_context**（CLI 传的）
3. **Buyer-derived**：recipient_company / recipient_region / sector / project_name / contact_name

未知变量保留 `{{var}}` 占位，运行后输出会列在 `missing_variables[]`。

---

## Output schema

```json
{
  "$schema": "hlzd/cold-outreach/v1-batch",
  "default_language": "en",
  "default_customer_type": "Manufacturer",
  "generated": 3,
  "failed": 0,
  "emails": [
    {
      "email": {
        "to": {"company": "Aramco", "contact": "Mr. Ahmed", "country": "Saudi Arabia"},
        "language": "en",
        "customer_type_used": "EPC",
        "subject": "EPC partner for your project - OCTG casing supply",
        "body": "Dear Mr. Ahmed,\n\nWe understand Aramco is executing your project...",
        "word_count": 69,
        "within_word_limit": true,
        "missing_variables": ["past_project_references"]
      },
      "followup_sequence": [
        {"day": 7, "subject": "Re: ...", "body": "...", "word_count": 32},
        {"day": 14, "subject": "Closing the loop - ...", "body": "...", "word_count": 25}
      ],
      "recommendation_next_step": "hlzd-cold-outreach"
    }
  ],
  "errors": []
}
```

---

## Word limits

| 类型 | 长度 |
|---|---|
| 单封邮件 body | 50-150 词 |
| Day 7 跟进 | 30-90 词 |
| Day 14 跟进 | 25-80 词 |

`within_word_limit: bool` 字段辅助检查。**不会硬阻断**，仅 advisory（人工 review 时关注）。

---

## Sample integration

```bash
# 1. 找买家
py ../hlzd-buyer-finder/scripts/cli.py --product "OCTG casing" --country SA

# 2. 背调
py ../hlzd-customer-due-diligence/scripts/cli.py --input buyers.json

# 3. 写邮件
py scripts/cli.py --input diligence.json \
    --product "OCTG casing" --sender-company "HLZD" \
    --output outreach.json --pretty
```

完整闭环：**调研 → 买家 → 背调 → 邮件**。

---

## Voice Contract (继承自 hlzd-market-report)

继承 LAWS：
- LAW 1 / LAW 2 (em-dash → ` - `) 已强制
- LAW 3 (inline link) — 邮件正文未强制（邮件体格式更灵活）
- LAW 5 (claim 需 evidence) — 模板中 `[past project references]` 占位让人工填证据
- LAW 7 (no brand assumption) — 默认 sender 用 cli 参数显式指定，不假设

---

## Anti-patterns / Limitations

| 限制 | 处置 |
|---|---|
| 邮件仅生成草稿，不自动发送 | v0.2 接 SendGrid / Mailgun |
| 模板是英文友好的 en/es；非西语 / 非英语国家要手动改 | v0.2 加 ar / zh / ru / pt |
| 跟进序列是固定 Day 7 / Day 14，不接邮件打开数据触发 | v0.2 接 SMTP webhook |
| LinkedIn / WhatsApp / SMS 不发 | 单独 v0.2 Skill |
| `missing_variables` 不阻断 — 仍可能含 placeholder | 二次 review 强制要求替换 |

---

## Related Skills

```
┌────────────────────────┐
│  hlzd-customer-due-    │  ← 上游：buyer A/B 级
│  diligence              │
└────────────┬───────────┘
             │
             ▼
┌────────────────────────┐
│ ★ hlzd-cold-outreach ★ │  ← 本 Skill
│  5 类模板 + 跟进序列    │
└────────────────────────┘
             │
             ├── 内部流转：人工 review + SendGrid
             └── v0.2：自动 send / 多语种 / LinkedIn template
```

**前置**：`hlzd-customer-due-diligence`（Grade A/B 买家）
**后继**：人工 review + 邮件 send 工具

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：6 类模板 × 2 语种 + Day 7/14 跟进 + 变量替换 |

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
