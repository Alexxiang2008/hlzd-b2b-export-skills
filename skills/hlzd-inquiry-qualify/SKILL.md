---
name: hlzd-inquiry-qualify
description: "解析 B2B 工业品询盘（RFQ / 邮件 / 聊天 / WhatsApp），自动提取产品/数量/规格/目的港/贸易术语/联系人/公司，按 5 维（产品需求 / 商务需求 / 技术需求 / 客户信息 / 项目背景）打出 A/B/C/D 四级评分（A 最优质），并生成待向客户反向确认的问题清单。Use when 用户说'询盘评分'、'RFQ 评估'、'这个询盘值不值得跟'、'帮我看看这封邮件'、'qualify this inquiry'、'B2B lead scoring'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: lead-qualification
  triggered_by:
    - 询盘评分
    - RFQ评估
    - RFQ评分
    - 询盘质量
    - 这个询盘值不值得跟
    - 帮我看看这封邮件
    - qualify inquiry
    - B2B lead scoring
    - inquiry qualification
    - RFQ parsing
---

# HLZD 询盘评估（Inquiry Qualification）

把一封 B2B 工业品询盘（RFQ / 邮件 / WhatsApp / 微信片段）从「不可读的对话」变成「可决策的结构化对象」——5 维评分 + 待确认问题清单 + CRM-ready JSON。

---

## When to use

调用本 Skill 当用户：

- 拿到一封海外询盘邮件想判断「值不值得跟」
- 一次性收到多封询盘需要批量排序
- 想要补齐询盘里缺失的技术参数（工作压力/温度/介质/认证）
- 想给销售团队一套统一的「询盘分级」SOP
- 在开发自定义 CRM / 邮件机器人 / WhatsApp 客服助手

**不要调用本 Skill 当**：

- 用户只想要语言翻译（用 hlzd-translation-factory，二期）
- 用户想要的是邮件模板生成（用 hlzd-cold-outreach）
- 询盘已经定型，正准备报价（用 hlzd-quotation-gen）

---

## How this skill is invoked

```
/hlzd-inquiry-qualify <inquiry-file-or-stdin>
```

示例：

```bash
# 从文件读取
/hlzd-inquiry-qualify ./inquiry.txt

# 从 stdin 接收（剪贴板粘入）
pbpaste | /hlzd-inquiry-qualify

# 在 Claude Code / Codex / Cursor 中直接说：
#   "帮我评分这封询盘" → 自动调本 Skill
```

也可以由其他 Skill 触发（沿 HLZD 内部调用约定）：

```
hlzd-cold-outreach 收到回复 → 推入 hlzd-inquiry-qualify → 评分 < B 提醒人工
```

---

## The 5-dimension scoring rubric

| 维度 | 满分 | 评分要点 |
|---|---|---|
| **D1 产品需求** | 25 | 产品名称 + 规格型号 + 数量（明确 > 模糊 > 缺失）|
| **D2 商务需求** | 25 | 目的港 + 贸易术语 + 目标价 / 预算区间 + 期望交期 |
| **D3 技术需求** | 25 | 应用场景 + 认证要求 + 关键工况（压力 / 温度 / 介质）|
| **D4 客户信息** | 15 | 公司名 + 联系人 + 职位 + 邮箱 / 电话 + LinkedIn / 官网 |
| **D5 项目背景** | 10 | 项目名 / 项目阶段 / EPC/PMC / 招标号 / 时间线 |

**评级阈值**：

| 等级 | 总分 | 判定 |
|---|---|---|
| **A** | 90-100 | 立即分配销售 + 24h 内首次回复 |
| **B** | 70-89 | 可分配给销售 + 48h 内回复，需补 D3 信息 |
| **C** | 50-69 | 培育池 / 邮件营销 / 补全后再评 |
| **D** | 0-49 | 归档 / 模板回 / 转入自动 nurture |

详细规则见 `references/scoring-rubric.md`。

---

## Output schema（CRM-ready JSON）

```json
{
  "$schema": "hlzd/inquiry-qualify/v1",
  "raw_text_hash": "sha256:...",
  "detected_language": "en",
  "extracted": {
    "product": {
      "name": "API 5CT OCTG Casing",
      "specifications": ["L80", "9 5/8 inch", "BTC connection"],
      "quantity": "5000 meters",
      "hs_code_suggestion": "730429"
    },
    "commercial": {
      "destination_port": "Jeddah, Saudi Arabia",
      "incoterm": "CIF",
      "target_price": null,
      "expected_delivery": "2026-Q3"
    },
    "technical": {
      "application": "oilfield / downhole",
      "certifications_required": ["API 5CT", "ISO 11960"],
      "operating_conditions": {
        "pressure": null,
        "temperature": null,
        "media": "sour service (H2S)"
      }
    },
    "customer": {
      "company_name": "Saudi Aramco Trading Co.",
      "contact_person": "Mr. Ahmed",
      "title": "Procurement Manager",
      "email": "ahmed@aramco.example",
      "phone": null,
      "linkedin": null,
      "country": "SA"
    },
    "project_context": {
      "project_name": "South Ghawar Field Expansion",
      "project_phase": "tender",
      "epc_or_pmc": null,
      "tender_ref": null,
      "timeline": "12 months"
    }
  },
  "scoring": {
    "D1_product":   { "score": 22, "max": 25, "missing": ["exact OD"] },
    "D2_commercial":{ "score": 18, "max": 25, "missing": ["target_price"] },
    "D3_technical": { "score": 20, "max": 25, "missing": ["operating_pressure"] },
    "D4_customer":  { "score": 12, "max": 15, "missing": ["linkedin"] },
    "D5_project":   { "score":  8, "max": 10, "missing": ["tender_ref"] },
    "total": 80,
    "grade": "B",
    "grade_reason": "Strong commercial terms but missing target price and operating pressure."
  },
  "questions_to_confirm": [
    "Could you share the target unit price (USD/meter) for budget alignment?",
    "What is the maximum operating pressure (psi) of the well?",
    "Do you require sour service certificate (NACE MR0175)?",
    "Is there a tender reference number we should quote against?",
    "Who is the final end-user of this order (Aramco direct or via EPC)?"
  ],
  "red_flags": [],
  "compliance_check": {
    "two_use_items": false,
    "sanctioned_country_buyer": false,
    "sanctioned_entity_buyer": false,
    "passed": true,
    "notes": []
  },
  "recommended_next_skill": "hlzd-customer-due-diligence"
}
```

完整字段定义见 `inquiry_parser.py` 中 Pydantic models。

---

## How it works

1. **语言检测** — langdetect（或基于关键词 fallback），决定后续正则语言包
2. **结构抽取** — 关键词 + 正则 + 单位识别（mm/inch/MPa/psi/℃/℉）
3. **5 维评分** — 缺失字段反向扣分，达到阈值出评级
4. **待确认问题** — 按缺失维度排序，前 5 高优先级
5. **合规预检** — 内置出口管制关键词（OCTG / dual-use）+ 制裁国家名单（OFAC SDN）+ 制裁实体（模糊匹配）
6. **推荐下一步** — Grade ≥ B 推 customer-due-diligence，C 推 nurture，D 建议模板回复

---

## Sample inputs

| 类型 | 文件 | 期望输出 |
|---|---|---|
| 优质沙特油气询盘 | `assets/inquiry_samples/01-saudi-rfq.txt` | Grade A/B，D3 缺失 2 项 |
| 噪音/无关键信息 | `assets/inquiry_samples/02-noise-low-quality.txt` | Grade D，C 项全空 |
| 多语种（西班牙） | `assets/inquiry_samples/03-es-latam.txt` | 语言识别 ES，正常抽取 |

### 快速跑通

```bash
cd skills/hlzd-inquiry-qualify
python scripts/inquiry_parser.py --input assets/inquiry_samples/01-saudi-rfq.txt
python scripts/inquiry_parser.py --input assets/inquiry_samples/01-saudi-rfq.txt --pretty
python scripts/inquiry_parser.py --stdin < assets/inquiry_samples/02-noise-low-quality.txt
```

期望输出（截选）：

```
{
  "detected_language": "en",
  "extracted": { ... },
  "scoring": { "total": 80, "grade": "B" },
  "questions_to_confirm": [ ... 5 items ],
  "compliance_check": { "passed": true, ... },
  "recommended_next_skill": "hlzd-customer-due-diligence"
}
```

---

## Red-flag phrases（内置）

| 类别 | 关键词样例 | 处置 |
|---|---|---|
| 出口管制（敏感品类）| OCTG, dual-use, two-use, encryption module | `red_flags[]` 提示 + 合规模块可拒绝处理 |
| 制裁国家买家 | North Korea, Iran, Syria, Cuba, Crimea, Donetsk, Luhansk | `compliance_check.passed = false` |
| 制裁实体（模糊匹配）| 见 `data/red-flag-phrases.json`（OFAC SDN 抽样）| `sanctioned_entity_buyer: true` 时强制中断 |
| 欺诈高风险 | "test order", "100% advance", "wire to personal account" | `red_flags[]` 中等警示 |

> ⚠️ **红线产品/真实制裁名单请勿依赖本 Skill 自行判断**，正式合规复核必须接 `hlzd-trade-compliance`（W8 实现）。本 Skill 仅做**第一道粗筛**，输出末尾必须注明"未替代合规复核"。

---

## Related Skills（依赖图）

```
hlzd-cold-outreach
        │ 收到回复
        ▼
┌─────────────────────────┐
│  hlzd-inquiry-qualify   │  ◄── 本 Skill
└────────┬────────────────┘
         │
   ┌─────┼─────────┬───────────┬───────────────┐
   ▼     ▼         ▼           ▼               ▼
 due     solution  quotation  trade         nurture
 diligence match    gen        compliance    (no skill)
   │       │          │           │
   ▼       ▼          ▼           ▼
  按 ICP   按工况    按市场      按 HS / OFAC
  评级    匹配 3 套 价格/利润    INCOTERMS
          方案     / 账期       监管条件
```

**前置**:  `hlzd-cold-outreach`（回复触发）
**后继**:  `hlzd-customer-due-diligence` / `hlzd-solution-match` / `hlzd-trade-compliance` / 模板回复（Grade D）

---

## Boundaries & Limitations

- **本 Skill 不是 LLM**：所有抽取走确定性规则（regex/keyword/numeral）。LLM 仅在「可选补全」时通过 prompt 调用，不参与决策。
- **本 Skill 不替代合格合规官**：制裁名单为静态快照，必须每月同步最新 OFAC/EU/UN 公告。
- **本 Skill 不读取历史邮件**：仅基于当次输入。若需对话历史，请传入完整 mail thread。
- **本 Skill 不区分同名公司**：如客户写「Aramco」指 Saudi Aramco 还是 Aramco Trading 需人工确认。

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：5 维评分 + 多语种正则抽取 + 合规粗筛 |

详细变更见仓库根 `VERSIONS.md`。

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform, 2026.*
