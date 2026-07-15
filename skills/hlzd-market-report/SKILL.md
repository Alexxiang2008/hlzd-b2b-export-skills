---
name: hlzd-market-report
description: "B2B 工业品海外市场情报报告生成 —— 9 节结构 HTML 自包含报告（cover / TOC / signals / platforms / comparison / actions / methodology / sources）+ Markdown 简化版。从 hlzd-b2b-research 输出或原始 web 信号自动组装。Use when 用户说'出报告'、'海外调研报告'、'市场情报'、'跨境选品报告'、'做份 deliverable'、'跨境市场扫描 HTML'、'generate B2B market report'、'market intelligence brief'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: report-generation
  triggered_by:
    - 出报告
    - 海外调研报告
    - 市场情报
    - 跨境选品报告
    - 跨境市场扫描
    - HTML 报告
    - B2B market report
    - market intelligence brief
    - generate report
    - deliverable
---

# HLZD 市场情报报告

把"调研出来的信号"组装成 9 节自包含 HTML 报告，便于发给客户、董事会议或朋友圈。

---

## When to use

调用本 Skill 当用户：

- 跑完 `hlzd-b2b-research` 拿到 JSON，想打包成可视报告
- 跑完 `hlzd-buyer-finder` 拿到买家名单，想附市场分析
- 要给客户/老板看"我做了什么"的市场扫描
- 想在 5 分钟内交付一份**视觉 + 数据** 都达标的报告

**不要调用本 Skill 当**：

- 用户只想要一份**纯文本**摘要 —— 用 `hlzd-b2b-research` 的 Markdown 输出即可
- 用户要做**实时仪表盘** —— 这是静态报告（v0.1）

---

## How this skill is invoked

```bash
# 全自动：topic + 关键词 → 一键 HTML + Markdown
py scripts/pipeline.py --topic "OCTG casing export to UAE" \
                        --keywords "OCTG casing" "API 5CT" "Aramco tender" \
                        --output-html report.html --output-md report.md

# 复用 hlzd-b2b-research 的 JSON
py scripts/pipeline.py --topic "auto" \
                        --from-research b2b-research-output.json \
                        --output-html report.html
```

---

## 9-节报告结构

```
┌── Cover ────────────────────────┐
│  ★ Headline (L1: 56-72px)         │
│  Tagline (L2: 16-18px)            │
│  4 KPI cards                      │
│  3-step action plan (L1 action)    │
│  Meta line (L3: 13px)              │
└────────────────────────────────┘
       ↓
TOC  (9 anchored links)
       ↓
1. Solution Overview
   - Recap (16-18px)
   - 5-row conclusion table
       ↓
2. 3 Core Signals
   - User pain quote (blockquote)
   - Root cause
   - Market implication
   - Source chips
       ↓
3. Platform Deep Dive (×4-5 platforms)
   - Stat chip
   - 5 findings each (with inline source link)
       ↓
4. Strategic Comparison Table
   - 10 dimensions × 3 vendors
       ↓
5. 3-Step Action Plan
   - Green card with options / risk / execution
       ↓
6. Methodology & Limitations
   - 5-step process / 5-dim signal judgement / 7-limitations
   - Yellow callout box
       ↓
7. Sources (grouped by category)
   - Sources grid
       ↓
Footer (HLZD brand + license)
```

---

## Output schema (input 数据契约)

```json
{
  "$schema": "hlzd/market-report/v1",
  "meta": { "topic": str, "audience": str, "window_days": int, "language": str },
  "cover": {
    "headline": str, "tagline": str,
    "kpis": [ {"label": str, "value": str, "unit": str?}, ... ],
    "three_step_plan": [ {"step": str, "action": str}, ... ]
  },
  "toc": [ {"id": str, "title": str}, ... ],
  "solution_overview": {
    "recap": str,
    "conclusion_table": [ {"metric": str, "finding": str, "implication": str}, ... ]
  },
  "three_signals": {
    "signals": [
      { "title": str, "user_pain_quote": str, "root_cause": str,
        "market_implication": str, "sources": [ {"name": str, "url": str}, ... ] }
    ]
  },
  "platform_deep_dive": {
    "platforms": [
      { "name": str, "stat": str,
        "findings": [ {"headline": str, "body": str, "source_name": str, "source_url": str}, ... ] }
    ]
  },
  "strategic_comparison": {
    "vendors": [ { "name": str, "attr_1": str, ... }, ... ],
    "attributes": [str, ...]
  },
  "action_plan": {
    "actions": [ {"title": str, "options": [str, ...], "risk": str, "execution": str}, ... ]
  },
  "methodology": {
    "five_step": [str, ...], "five_dim": [str, ...], "seven_limitations": [str, ...]
  },
  "footer_sources": {
    "sources": [ {"name": str, "url": str, "category": str}, ... ]
  }
}
```

---

## Voice Contract (LAW 7 条)

继承自 b2b-overseas-market-report spec，落地为可执行检查：

| LAW | 含义 | 实施位置 |
|---|---|---|
| 1 | Body 开头 = "What I learned:" | `lib.check_law_1` |
| 2 | **永远**用 ` - ` 不用 em-dash / en-dash | `lib.normalize_dashes` 自动替换 |
| 3 | 引用必须 `[name](url)` inline link | `lib.md_link` |
| 4 | 无 trailing `Sources:` block（footer 替代） | `lib.check_law_4` |
| 5 | 每个 claim 必须有 URL 或 engagement signal | `lib.validate_voice_contract` |
| 6 | "best X 2026" 按信号质量排 | heuristic，由 agent 做 |
| 7 | 不假设用户是某个品牌 | `lib.validate_voice_contract` (brand_assumption) |

输出前 `validate_voice_contract()` 跑一遍，violations 列表可由 pipeline 选 warn 或 block。

---

## Integration with hlzd-b2b-research

```bash
# 跑完 b2b-research → 出 Markdown
py ../hlzd-b2b-research/scripts/run_research.py \
    --product "OCTG casing" --markets "UAE Saudi" \
    --output-json b2b-output.json

py scripts/pipeline.py --topic "auto" --from-research b2b-output.json \
    --output-html report.html --output-md report.md
```

`from_b2b_research()` adapter 自动把 b2b-research 的 `trade_data / trends / buyers` 转成 report schema：

- 每个 market = 一个 signal
- trade_data → platforms
- HS code + 中国份额 → comparison data

---

## Sample outputs

| 规模 | HTML | Markdown |
|---|---|---|
| Standard (auto) | ~14 KB | ~4 KB |
| With data (full) | ~16 KB | ~5 KB |

CSS 内嵌（自包含），无外部字体 / CDN 依赖。Print-friendly：自动翻转为高对比黑白版。

---

## Anti-pattern / Limitations

| 限制 | 处置 |
|---|---|
| Brave API 需要 `HLZD_BRAVE_API_KEY` | fallback 到 ddgs；都没有则手动输入信号 |
| pip install ddgs 是 v0.1 唯一可选外部依赖 | 需要网络爬取能力 |
| 报告不含 LLM 调用 — signals 是 heuristic 提炼 | 上层 Agent 可接 LLM 增强 `from_b2b_research` 提炼 3 core signals |
| Voice Contract 检查是 advisory — 不阻断 | 上层 Agent 可硬 fail 在 violation > 0 |
| 多人多语言一次性渲染：v0.1 仅 en 模板 | 二期加 zh / es / ar 多语言模板 |

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：9 节 HTML + 8 节 Markdown + 从 hlzd-b2b-research 接入 |

升级轨迹见仓库根 `VERSIONS.md`。

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
