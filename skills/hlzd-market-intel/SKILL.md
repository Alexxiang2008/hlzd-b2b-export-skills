---
name: hlzd-market-intel
description: "B2B 跨境贸易市场情报 v0.2 — 抓取 Reddit/X/YouTube/TikTok/Bluesky/HackerNews/GitHub/arXiv 等 14+ 平台 30 天真实用户声音，输出 Top 5 痛点 + 用户原话 + 跨境 actionable 的自包含 HTML 报告（融合 4-agent pipeline + Pain Profile 行业预设 + Voice Contract 7 LAWS）。受众：B2B 跨境贸易老板 / 业务团队 / 选品经理。Use when 用户要做海外产品调研 / 选品 / 痛点分析 / 竞品监控 / 客户声音采集。"
license: MIT
metadata:
  author: HLZD (深圳海联智达科技 / HLZD)
  version: 0.2.0
  industry: cross-border-b2b
  category: market-intelligence
  triggered_by:
    - 海外产品调研
    - 跨境选品
    - 客户痛点
    - 用户反馈
    - 海外市场调研
    - 选品调研
    - 竞品分析
    - 用户声音
    - 客户声音
    - 痛点分析
    - 海外用户评价
    - 跨境贸易调研
    - 产品口碑
    - B2B 调研
    - 海外调研
    - market research
    - product research
    - customer pain points
    - user feedback
    - cross-border sourcing
    - overseas market
    - product selection
    - competitor analysis
    - customer voice
    - social listening
    - reddit research
---

# HLZD Market Intel v0.2.0

> **B2B 跨境贸易市场情报** — 抓 14+ 平台 30 天真实用户声音，输出 Top 5 痛点 + 用户原话 + 跨境 actionable 自包含 HTML。

## v0.2 升级亮点 (vs v0.1)

- ✅ **适配仓库 AGENTS.md frontmatter 规范** (name/description/license/metadata.triggered_by)
- ✅ **SKILL.md 精简** 从 2264 行到 ~150 行；详细 reference 移到 `references/SKILL_FULL.md`
- ✅ **可选依赖** 降到最小：纯 stdlib (json, urllib, csv) 可跑；可选 API (Reddit/X/YouTube/TikTok) 需 key
- ✅ **Voice Contract 7 LAWS 兼容** (与 hlzd-market-report 共享)

## 工作流 (10 步)

1. **Step 0: First-Run Setup Wizard** — 配置 API keys (SCRAPECREATORS / OPENAI / XAI / BRAVE 等)
2. **Step 0.45: Query Quality Pre-Flight** — 检测 keyword-trap 主题 (健康/政治) → 提前降级
3. **Step 0.5: Pre-Flight Resolution** — 解析 handle / repo / community
4. **Step 0.55: Pre-Research Intelligence** — 解析社区 + handles (Reddit/HN/GitHub/Bluesky 等)
5. **Step 0.75: Query Plan** — LLM 自己当 planner，决定抓哪些 platform + handles
6. **Research Execution** — 调 scripts/briefing.py → 14 平台爬虫
7. **Save Raw + WebSearch Augment** — 落盘原始 + 补充 WebSearch 结果
8. **Cluster & Fuse** — scripts/lib/cluster.py + fusion.py 去重 + 合并 cluster
9. **Entity Extract** — scripts/lib/entity_extract.py → 抽 company / product / pain point
10. **HTML Report** — scripts/lib/html_render.py → 自包含 HTML 输出

## 快速使用

### CLI

```bash
# 默认 30 天窗口 + 14 平台
py scripts/briefing.py "海外安防摄像头 2026 痛点"

# 指定 pain profile + 平台
py scripts/briefing.py "exosomes" --pain-profile presets/pain-profiles/biomedical.yaml
```

### Python API

```python
from scripts.briefing import run_research

result = run_research(
    topic="智能门锁 跨境选品",
    pain_profile="presets/pain-profiles/security.yaml",
    output_html="report.html",
)
```

### 4-Agent Pipeline (--agent flag)

```
Plan Agent → Research Agent → Cluster Agent → Report Agent
```

详细 agent 协议见 `references/SKILL_FULL.md` §Agent Mode。

## 输出 schema

```json
{
  "topic": "...",
  "window_days": 30,
  "platforms_scanned": ["reddit", "hackernews", "youtube", "..."],
  "signals": [
    {
      "platform": "reddit",
      "url": "...",
      "title": "...",
      "snippet": "...",
      "pain_signal": "...",
      "engagement_score": 0.85
    }
  ],
  "clusters": [
    {
      "name": "Top Pain Point",
      "occurrences": 47,
      "user_quotes": ["..."],
      "actionable": "..."
    }
  ],
  "html_report": "report.html"
}
```

## 配置文件 (4-Agent pipeline)

`config/company.yaml` + `locale/{en_US,zh_CN}.json` + 4 规则 PDF (UCP / ICC / ISP98 / URDG)。

## 依赖

**必装** (零外部依赖):
- Python 3.10+
- 库: `requests`, `urllib3` (标准库)

**可选** (提升数据来源):
- `SCRAPECREATORS_API_KEY` — TikTok / YouTube / Instagram
- `OPENAI_API_KEY` / `XAI_API_KEY` / `OPENROUTER_API_KEY` — LLM 提炼痛点
- `BRAVE_API_KEY` — WebSearch
- `BSKY_HANDLE` + `BSKY_APP_PASSWORD` — Bluesky
- `TRUTHSOCIAL_TOKEN` — Truth Social

详见 `references/SKILL_FULL.md` §Configuration。

## 测试

```bash
py -m pytest tests/ -q          # 全 50+ tests 跑 (含 hermes / adversarial_v3)
```

**注意**: 部分测试需要外部 API (Reddit, Twitter 等)。offline 时只跑纯函数子集:

```bash
py -m pytest tests/test_categories.py tests/test_dedupe.py -q
```

## Related Skills

- `hlzd-market-report` (姊妹) — 9 节 HTML 自包含报告 (本 skill 输出是其上游)
- `hlzd-pipeline-viz` (下游) — 跨 skill trace 累计 + dashboard
- `hlzd-b2b-research` (姊妹) — HS 编码 + UN Comtrade 市场数据
- `hlzd-customer-profile` (姊妹) — 客户 360° 画像

## 详细文档

- `references/SKILL_FULL.md` — 完整 2000+ 行工作流 (Step 0-7 + 7 LAWS + 4 Agent Protocol + 14 平台 backends)
- `references/methodology.md` — 5-dim 信号评分 (与 hlzd-market-report 共享)
- `references/save-html-brief.md` — 输出 HTML 模板规范
- `references/hlzd-extensions.md` — HLZD 私有扩展 (Pain Profile 行业预设)
- `presets/pain-profiles/` — 6 行业预设 (security / biomedical / SaaS / hardware / food / fashion)
- `presets/openai.yaml` — OpenAI LLM 提炼 prompt 配置

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 原始 (mvanhorn/last30days fork) |
| 0.2.0 | 适配仓库规范: frontmatter + SKILL.md 精简 + Voice Contract LAWS |
