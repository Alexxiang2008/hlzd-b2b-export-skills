---
name: hlzd-buyer-finder
description: "B2B 工业品海外采购商挖掘 —— 基于 Alibaba 国际站 + Volza 海关数据 + ImportGenius 公开目录，三链路自动发现真实海外买家，输出结构化 buyer JSON 与 Markdown 报告。Use when 用户说'找买家'、'找海外采购商'、'挖进口商'、'找客户'、'Volza 找买家'、'海关数据'、'find overseas buyers'、'find importers'、'B2B lead generation'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: lead-generation
  triggered_by:
    - 找买家
    - 找海外买家
    - 找进口商
    - 海关数据
    - Volza找买家
    - 找竞对客户
    - B2B客户挖掘
    - find buyers
    - find importers
    - find overseas buyers
    - Volza buyer search
    - B2B lead generation
    - supplier competitor buyers
    - import data buyers
---

# HLZD 买家发现（Buyer Finder）

阿里 + Volza + 公开目录三链路找真实海外进口商。**不编造买家名** —— 仅返回实际抓到或明确 mock 的数据；所有数据源失败时输出 `warnings[]`，绝不静默骗你。

---

## When to use

调用本 Skill 当用户：

- 想把某个工业品卖到 **X 国**，要找该国的真实进口商
- 已知某个 **中国竞对**（如"厦门欣鸿金属"），想找他的海外买家清单
- 拿到 100+ 公司名列表，想 dedup / 评分 / 按 value 排序
- 想知道某个国家 / 关键词下的进口商规模与活跃度
- 跑 Volza / 阿里 自动化，但担心被反爬 / 限额

**不要调用本 Skill 当**：

- 用户要找 **中国卖家**（你是中国卖家视角，请改用 `hlzd-buyer-finder` 的反向场景 = 暂时没做）
- 用户只是要**单条买家信息查证** —— 用 `hlzd-inquiry-qualify` 反向灌入买家联系方式
- 用户要发**邮件 / WhatsApp** —— 应改用 `hlzd-cold-outreach`

---

## How this skill is invoked

```
/hlzd-buyer-finder <product> <target-country>
```

### 完整调用

```bash
# 链路 A (默认): 阿里发现竞对 → Volza 找买家
py scripts/cli.py --product "OCTG casing" --country US

# 链路 B: 用户指定竞对 → Volza 直接搜
py scripts/cli.py \
    --competitor "Xiamen Hym Metal Products Co., Ltd." \
    --competitor "Shenzhen Kaier Wo Prototyping Technology Co., Ltd." \
    --country US \
    --method competitor

# 链路 C: 关键词 + 国家直接搜（跳过竞对）
py scripts/cli.py --product "container house mining" \
                   --country AU \
                   --method keyword

# JSON 输出 + 输出到文件
py scripts/cli.py --product "OCTG" --country US \
                   --output-json buyers.json --pretty
```

---

## The 3-link pipeline

```
                  ┌─────────────────────────────┐
                  │     用户输入：产品 + 国家    │
                  └──────────────┬──────────────┘
                                 ↓
                ┌────────────────┴────────────────┐
                │   --method                       │
                ▼                  ▼               ▼
        ┌──────────────┐  ┌────────────────┐  ┌──────────────┐
        │ 链路 A: auto  │  │ 链路 B:        │  │ 链路 C:      │
        │               │  │ competitor     │  │ keyword      │
        │ 1. 阿里搜竞对  │  │                │  │              │
        │ 2. Volza找买家│  │ 用户提供竞对名 │  │ 关键词+国家   │
        └──────┬────────┘  └────────┬───────┘  └──────┬───────┘
               └──────────┬────────┴─────────┬───────┘
                          ↓                  ↓
                  ┌─────────────────────────────────┐
                  │  dedup_importers()              │
                  │  - normalize company name        │
                  │  - 取 max value 保留版本         │
                  │  - 按 USD 价值降序              │
                  └────────────────┬────────────────┘
                                   ↓
                    ┌──────────────────────────┐
                    │ JSON (schema hlzd/.../v1) │
                    │ + Markdown 报告            │
                    │ + warnings[] (缺失依赖说明) │
                    └──────────────────────────┘
```

### 链路 A：auto（默认）

适用：**不知道竞对 + 想要广撒网**

```bash
py scripts/cli.py --product "CNC machining" --country US
```

步骤：
1. **Alibaba 搜竞对**（https://www.alibaba.com/trade/search）：抽取中国供应商公司名，最多 5 家
2. **每个供应商 → Volza 搜买家**（https://www.volza.com/search?q=...）：取该供应商的历史进口商清单
3. 全局 dedup → 按 USD 价值排序

限额：
- Alibaba：每天 5 次搜索
- Volza：每天 10 次搜索（免费版）

fallback：阿里被 captcha → 自动 seed 一个"`Product` Co., Ltd." → 继续 Volza，避免管线中断。

### 链路 B：competitor

适用：**已知竞对 + 想跟单他们的客户**

```bash
py scripts/cli.py \
    --competitor "Xiamen Hym Metal Products Co., Ltd." \
    --competitor "Shenzhen Kaier Wo Prototyping Technology Co., Ltd." \
    --country US \
    --method competitor
```

跳过阿里，竞对名直接来自 CLI 输入。

### 链路 C：keyword

适用：**无竞对信息、关键词范围搜索**

```bash
py scripts/cli.py --product "container house mining" \
                   --country AU \
                   --method keyword
```

直接按国家 + 关键词搜进口商，**不依赖竞对名**。

---

## Output schema

```json
{
  "$schema": "hlzd/buyer-finder/v1",
  "product": "OCTG casing",
  "country": "US",
  "method": "auto",
  "competitors": [
    { "company_name": "Xiamen Hym Metal Products Co., Ltd.", "source": "alibaba.com" }
  ],
  "importers": [
    {
      "importer_name": "ABC Machinery Inc",
      "country": "United States",
      "origin_country": "China",
      "quantity": "500 units",
      "value": "$125,000",
      "date": "2025-03",
      "source": "volza.com",
      "matched_competitor": "Xiamen Hym Metal Products Co., Ltd."
    }
  ],
  "warnings": [
    "volza_blocked (free-tier limit; upgrade Volza Pro or use ImportGenius / 52WMB)"
  ],
  "stats": {
    "competitors_found": 5,
    "importers_found_pre_dedup": 23,
    "importers_after_dedup": 12,
    "volza_quota_used": 5,
    "alibaba_quota_used": 1
  }
}
```

JSON 输出到 `buyers.json`，warnings 详细列出每个失败来源与备选。

---

## Rate limiter & 反爬护栏

`lib.RateLimiter` 自动强制：

| 数据源 | 最小间隔 | 每日配额 | 状态保留 |
|---|---|---|---|
| Alibaba | 10s | 5 次 | `~/.cache/hlzd-buyer-finder/rate_state.json` |
| Volza | 5s | 10 次 | 同上 |

**Volza blocked detection**（`lib.classify_volza_response`）：

| 返回 body 长度 | 判定 | 处置 |
|---|---|---|
| 11055 ± 200 bytes | `blocked` | warning + skip，提示升级 Pro / 用 ImportGenius |
| ≥ 15000 | `success` | 抽取表格 |
| 中间区间 | `loading` | 重试 |

为什么这是 deterministic：Volza 屏蔽固定返回首页，长度 11055 是经验值。**无需网络即可单测**。

---

## Anti-scraping notes（来自 customs-data-find SOP）

| 风险 | 处置 |
|---|---|
| Alibaba captcha | 立即返回 warning；推荐手动登录或换 Volza |
| Volza free-tier 屏蔽 | 检测 11055 长度 → 提示升级 Pro |
| 阿里反爬（cookie / JS） | 推荐 Playwright；本 v0.1 仅做纯 HTML 抓取 |
| ImportGenius / 52WMB | 接口占位见 `sources/keyword.py`，二期接入 |
| 日配额已用完 | state 文件持久化配额，跨 CLI 调用共享 |

---

## Sample outputs

见 `assets/sample-outputs/`（占位，可附真实脱敏案例）。

---

## Related Skills

```
        ┌─────────────────────────┐
        │  hlzd-b2b-research       │  ← 上游：先调研（HS、市场规模）
        │  4步 pipeline 出报告       │
        └────────────┬────────────┘
                     │ 衔接：国家 / 关键词
                     ▼
        ┌─────────────────────────┐
        │ ★ hlzd-buyer-finder ★  │  ← 本 Skill：找买家
        │ 3 链路 找真实采购商      │
        └────────────┬────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   customer         cold-        (next) query enrichment
   due-diligence    outreach     via LinkedIn / email
   (验证买家真实性)   (发邮件)
```

**前置**：`hlzd-b2b-research` 提供国家 / 产品 / HS context
**后继**：`hlzd-customer-due-diligence`（验证买家真实性）/ `hlzd-cold-outreach`（发开发信）

---

## Boundaries & Limitations

- **本 Skill 不是买家真实性认证**：Volza 数据可能滞后 / 来源仅反映历史，需配合 `hlzd-customer-due-diligence` 验证（域名 / 公司注册 / LinkedIn）。
- **本 Skill 不发邮件**：仅给买家名单，触达请用 `hlzd-cold-outreach`。
- **本 Skill 不抓 LinkedIn**：占位二期扩展。
- **Volza 免费版限制**：每天 10 次搜索；详细联系方式需付费。要解更多字段请升级 Pro 或切 ImportGenius / 52WMB（接口已声明，待接入）。
- **Alibaba 反爬**：纯 HTML 抓取可能被 captcha；如失败推荐切到 Playwright 版本（v0.2 计划）。
- **数据集滞后**：Volza 数据延迟约 1 个月；新买家可能未及时反映。

---

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：3 链路 + urllib 实现 + 离线可单测 + 跨 CLI 配额持久化 |

升级轨迹见仓库根 `VERSIONS.md`。

---

*Crafted for B2B industrial exporters — HLZD Cross-Border AI Platform · 2026*
