---
name: hlzd-b2b-research
description: "B2B 工业品海外市场调研全链路自动化 —— HS 编码查询（hsbianma.com）+ UN Comtrade 市场规模 + Google Trends 需求热度 + DDGS 买家线索 + 招标信息追踪，输出结构化 JSON 与 Markdown 报告。Use when 用户说'B2B 调研'、'工业品市场分析'、'查 HS 编码'、'查采购商'、'找海外买家'、'市场容量'、'招标追踪'、'B2B market research'、'industrial export research'、'find buyers overseas'、'project tender tracking'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: market-research
  triggered_by:
    - B2B调研
    - 工业品调研
    - 市场容量
    - 进口数据
    - 查采购商
    - 找海外买家
    - 集装箱房屋市场
    - 钢结构出口市场
    - 石油设备出口
    - 项目招标追踪
    - 目标市场分析
    - 海外采购商
    - HS编码查询
    - 询盘分析
    - B2B market research
    - industrial export research
    - find buyers overseas
    - project tender
    - import data
    - trade statistics
---

# HLZD B2B 工业品海外调研

把"卖什么？卖到哪？卖给谁？"在 30 秒内跑出 4 段数据：HS 编码 → 进口规模 → 需求热度 → 真实买家。

---

## When to use

调用本 Skill 当用户：

- 要把某个工业品卖到海外，需要先**判断市场规模 + 中国出口位置**
- 手里有几个目标市场（UAE / 沙特 / 尼日利亚 / 巴西…），需要并行调研
- 需要 HS 编码 + 监管条件 + 退税率
- 需要从 Google / LinkedIn 找真实买家（非 Alibaba / Made-in-China 平台供应商）
- 需要追踪政府 / World Bank / ADB 项目招标
- 需要把多次调研结果汇总成一份可发给客户的报告

**不要调用本 Skill 当**：

- 用户只要**单一数据点**（如"今天美元汇率"）—— 直接用单子脚本
- 用户只要 LLM 文本生成（不要当成 prompt 模板）
- **消费品出海**（应改用 `hlzd-market-report`）

---

## How this skill is invoked

```
/hlzd-b2b-research "<product>" [markets...]
```

### 单独子能力

| 任务 | 直接调用 |
|---|---|
| HS 编码 | `py scripts/hs_lookup.py --keyword "石油套管"` |
| Comtrade 贸易数据 | `py scripts/trade_data.py --hs 730429 --reporter sa --period 2023` |
| Google Trends | `py scripts/keyword_trends.py --kw "OCTG pipe" "API 5CT" --geo US --delay 12` |
| 买家 + 招标 | `py scripts/buyer_search.py --query "container house mining" --market "Australia Africa" --tenders --max 30` |

### 完整 pipeline（一键出报告）

```bash
py scripts/run_research.py \
    --product "OCTG casing" \
    --markets "UAE Saudi" \
    --hs-candidate 730429 \
    --output-md report.md \
    --output-json report.json \
    --pretty
```

输出示例：

```json
{
  "product": "OCTG casing",
  "markets": ["UAE", "Saudi"],
  "hs_code_used": "730429",
  "hs_code_candidates": [...],
  "trade_data": { "UAE": { ... }, "Saudi": { ... } },
  "trends": { "UAE": { ... }, "Saudi": { ... } },
  "buyers": { "UAE": { "total_buyers": 18, "buyers": [...] },
              "Saudi": { "total_buyers": 12, "buyers": [...] } },
  "warnings": []
}
```

---

## The 4-step pipeline

```
                  ┌──────────────────┐
   product name ─→│  Step 1: HS 编码  │ → 6位 HS Code + 监管条件 + 退税率
                  └────────┬─────────┘
                           ↓
                ┌──────────────────────────┐
                │   per-market (循环)       │
                │                           │
                │  Step 2: UN Comtrade      │ → 进口总额 + 中国份额排名
                │  Step 3: Google Trends    │ → 平均热度 + 相关上升词
                │  Step 4: DDGS 买家 + 招标  │ → 真实买家 URL + 类型
                └──────────────────────────┘
                           ↓
              ┌─────────────────────────┐
              │ 报告 (JSON + Markdown)  │ → data-driven 决策
              └─────────────────────────┘
```

### Step 1 — HS 编码查询（hs_lookup.py）

数据源：**hsbianma.com**（中文品名 → 完整 10 位 HS 编码 + 监管条件 + 退税率 + 状态）

```bash
py scripts/hs_lookup.py --keyword "石油套管" --pages 2
```

输出字段：

```json
[{
  "hs_code": "7304.29.10",
  "name": "石油套管",
  "unit": "千克",
  "rebate": "0",
  "regulation": "4,x",
  "expired": false
}]
```

> UN Comtrade API 用 HS 编码**前 6 位**（如 `7304.29.10` → `730429`）。

### Step 2 — UN Comtrade 市场规模（trade_data.py）

数据源：**UN Comtrade API**（comtradeapi.un.org），免费，无需 Key

```bash
py scripts/trade_data.py --hs 730429 --reporter sa --period 2023 --output data.json
```

常用国家简写：us / ae / sa / ng / za / au / br / mx / cn / world

输出字段（JSON）：

```json
{
  "hs_code": "730429",
  "reporter": "sa",
  "total_import_value_usd": 1234567890.0,
  "data_source": "UN Comtrade",
  "countries": [
    { "country": "China", "import_value_usd": 5e8, "share_pct": 41.7 },
    { "country": "Japan", "import_value_usd": 3e8, "share_pct": 25.0 }
  ]
}
```

关键解读：
- 进口总额 > 1 亿美元 → 大市场
- 中国份额 > 30% → 进入有空间但竞争激烈
- 中国份额 < 10% → 进入机会大但需要认证突破

### Step 3 — Google Trends 需求热度（keyword_trends.py）

数据源：**Google Trends**（pytrends），免费

```bash
py scripts/keyword_trends.py --kw "OCTG pipe" "API 5CT casing" --geo US --delay 12
```

⚠️ **429 限流保护**：每个关键词查询间隔 **≥12 秒**，触发 429 后等待 90 秒重试 3 次。

输出字段：

```json
{
  "keyword": "OCTG pipe",
  "interest_over_time": { "<date>": 65, ... },
  "related_queries": [ { "query": "API 5CT", "value": "+250%" } ],
  "interest_by_region": { "Saudi Arabia": 100, "UAE": 85 }
}
```

### Step 4 — DDGS 买家 + 招标信息（buyer_search.py）

数据源：**DuckDuckGo（ddgs 包）**，免费无 Key

```bash
py scripts/buyer_search.py \
    --query '"OCTG casing"' --market "Saudi Arabia UAE Nigeria" \
    --max 30 --tenders --delay 4
```

买家类型分类：

| 类型 | 关键词 | 价值 |
|---|---|---|
| 矿业/油田营地 | mining / oilfield / camp | 主力买家，批量采购 |
| EPC/总包 | EPC / contractor / turnkey | 项目驱动，决策链长 |
| 政府/NGO | government / World Bank / ADB | 大单，需合规认证 |
| 贸易商 | importer / trading house | 中间渠道，快速起量 |
| 酒店/文旅 | hotel / resort / glamping | 需求稳定 |
| 石油设备商 | OCTG / API 5CT / line pipe | 专用品类 |

内置过滤规则（自动跳过供应商页面）：
- ❌ alibaba / made-in-china / globalsources / ec21
- ❌ "shipping container"（集装箱房屋类常误匹配）
- ❌ "door casing"（casing 类常误匹配建筑装饰）

---

## Output schema

完整 pipeline 输出（`run_research.py`）：

```json
{
  "$schema": "hlzd/b2b-research/v1",
  "product": "<原始产品名>",
  "markets": ["<market1>", "<market2>", ...],
  "hs_code_used": "<最终使用的 6 位 HS>",
  "hs_code_candidates": [ {...}, ... ],
  "trade_data": {
    "<market>": {
      "hs_code": "...",
      "reporter": "...",
      "total_import_value_usd": 0.0,
      "data_source": "UN Comtrade",
      "countries": [ { "country": "...", "import_value_usd": 0.0, "share_pct": 0.0 }, ... ]
    }
  },
  "trends": {
    "<market>": {
      "keyword": "...",
      "geo": "...",
      "interest_over_time": null or { ... },
      "related_queries": [ ... ],
      "interest_by_region": null or { ... },
      "error": null or "<error msg>"
    }
  },
  "buyers": {
    "<market>": {
      "total_buyers": 0,
      "total_tenders": 0,
      "buyers": [ { "title": "...", "url": "...", "snippet": "...", "buyer_type": "..." } ],
      "tenders": [ ... ]
    }
  },
  "warnings": [ "<step>:<market>: <reason>", ... ]
}
```

JSON 输出到 `report.json`，Markdown 报告到 `report.md`。

---

## Sample outputs

见 `assets/sample-outputs/`（真实历史调研，脱敏）。

---

## Red-flag handling

| 风险 | 处置 |
|---|---|
| UN Comtrade 0 记录 | 检查 HS 编码 / 年份；尝试 reporter=world |
| Pytrends 429 限流 | 自动等待 90 秒重试 3 次；继续运行其它步骤 |
| pytrends 数据 partial | 正常（Google 对低流量词标记 partial）|
| DDGS 返回 0 结果 | 换引号短语关键词；查 ddgs 包版本 |
| hsbianma.com 访问失败 | 改用 volza.com / 中国海关编码中心 |
| 卖家数据真实性 | 必查 buyer 官网 + LinkedIn 二次复核 |

---

## Related Skills

```
              ┌────────────────────────────┐
              │  hlzd-buyer-finder         │  (W2-3 升级中)
              │  基于海关数据找真实进口商    │
              └────────────────────────────┘
                          │ 衔接
                          ▼
              ┌────────────────────────────┐
              │  ★ hlzd-b2b-research ★    │  ← 本 Skill
              │  4 步 pipeline 出报告        │
              └────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  hlzd-cold-outreach  hlzd-inquiry-     hlzd-market-report
  (用买家名单写邮件)    qualify           (HTML 报告渲染)
                      (对进来的询盘评分)
```

**前置**：无（首步）
**后继**：`hlzd-buyer-finder` / `hlzd-cold-outreach` / `hlzd-inquiry-qualify` / `hlzd-market-report`

---

## Boundaries & Limitations

- **本 Skill 不是合规判定**：制裁国家粗筛仅在 hlzd-inquiry-qualify 末段
- **HS 编码建议**：自动爬取仅为初判，争议商品请人工复核中国海关税则 / WCO HS 委员会
- **Comtrade 数据滞后**：UN Comtrade 数据滞后约 1.5 年（最新通常为 T-1 年）
- **DDGS 容量**：免费版每天约 10 次搜索；多市场轮询要做限额控制
- **未启用 LLM**：所有抽取走确定性规则；LLM 仅用于最终报告文案的润色

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：4 脚本 + run_research orchestrator + lib.py（共享基础设施）|

升级轨迹见仓库根 `VERSIONS.md`。

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
