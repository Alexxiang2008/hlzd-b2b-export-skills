# 首发文案 / Launch Post

> 仓库：https://github.com/Alexxiang2008/hlzd-b2b-export-skills
> Tag: v0.4.0
> 发布时间：2026-07-15

下面给出**中文版**（投递 即刻 / 知识星球 / LinkedIn 中文受众）+ **英文版**（投递 Hacker News / Reddit r/ClaudeAI / IndieHackers）。复制前请检查最新仓库地址。

---

## 🇨🇳 中文版 — 「即刻」「知识星球」投递

> 在 GitHub 上给 B2B 工业品出海赛道补了 4 个 Agent Skill，全程零"findings"
>
> 我们把"中国工业品卖到全球"这件事拆成了 **21 个**待开发的 Agent Skill，本周交付了头 **4 个**：
>
> 🛡️ `hlzd-inquiry-qualify` — 一封 B2B 询盘邮件进来，按 5 维（产品/商务/技术/客户/项目）打 A/B/C/D 级，自动识别欺诈 / 制裁国家 / 双重用途 — 出口管制粗筛
>
> 📊 `hlzd-b2b-research` — HS 编码 + UN Comtrade 全球进口规模 + Google Trends 热度 + DDGS 买家 + 招标，4 步 pipeline 优雅降级（缺依赖只 warning 不崩）
>
> 🎯 `hlzd-buyer-finder` — 阿里 + Volza + 公开目录三链路。11055 字节 = Volza 被屏蔽确定性检测，无需网络也能单测
>
> 📝 `hlzd-market-report` — 9 节自包含 HTML 报告（cover/TOC/signals/platforms/comparison/actions/methodology/sources），Voice Contract 7 条 LAWS 强制
>
> **关键事实**：
>
> - GitHub 上搜索 B2B / industrial export / cross-border trade / supplier lead / market research / industrial export research —— 多种关键词组合全部 0 结果，这是**赛道首发**。
> - 同行 `coreyhaines31/marketingskills` 39k stars / 6k forks / 47 个 skill 全是 B2C 营销，留下了 B2B 工业品的彻底空白。
>
> **架构亮点**：
>
> - **零依赖首选** Python 3.10+，CLI 走 `--input file / --stdin` 双通道，输出 JSON 到 stdout
> - **graceful degradation** — 阿里 captcha + Volza 403 都是 warning 而不是崩，**绝不静默骗你**
> - **157 个 pytest 测试全过**
> - **零样本虚构** — 买家名 HS 编码等所有数据都是真实爬取或显式 mock
> - **MIT 协议** 商业可用
>
> **下一步 12 周 Roadmap**：W4-5 接 customer-due-diligence / cold-outreach，W8 上 trade-compliance 合规护栏。
>
> 🔗 https://github.com/Alexxiang2008/hlzd-b2b-export-skills
>
> #ClaudeSkills #B2B #工业品出海 #跨境贸易 #海联智达

---

## 🇬🇧 English — Hacker News / Reddit r/ClaudeAI / IndieHackers

> Show HN: 4 Agent Skills for B2B industrial export (zero-fill a 0-result GitHub search)
>
> I built 4 production-ready agent skills for the **B2B industrial export** niche — a market GitHub has completely missed. Search terms like "B2B sales enablement skill claude", "industrial export B2B", "cross-border trade skill", "manufacturing export sales playbook", "lead generation outbound industrial manufacturing", and 4 others all return **zero results**. The 47-skill `coreyhaines31/marketingskills` (39k stars) is fully B2C / digital products.
>
> The 4 shipped Skills cover the full buyer-research-to-report lifecycle:
>
> 1. **hlzd-inquiry-qualify** — parse a B2B RFQ email, score across 5 dimensions (product / commercial / technical / customer / project), grade A/B/C/D, route to next skill, multi-language (en / zh / es / ar / ru / pt) extraction, with compliance coarse-screen (sanctioned countries, dual-use items).
>
> 2. **hlzd-b2b-research** — 4-step pipeline: HS code lookup (hsbianma.com) + UN Comtrade market size + Google Trends demand heat + DDGS buyer leads + tender tracking. Gracefully degrades when external deps missing — produces `warnings[]` instead of crashing.
>
> 3. **hlzd-buyer-finder** — Alibaba → Volza → public directory, with a **deterministic Volza-blocked detector** (11055-byte body length) — fully offline-testable. Persistent cross-CLI quota state.
>
> 4. **hlzd-market-report** — 9-section self-contained HTML report + Markdown rendering, with **Voice Contract LAWS** as executable checks (e.g. `lib.normalize_dashes` enforces " - " not em-dash).
>
> Engineering quality:
>
> - Zero / minimal dependencies (stdlib Python 3.10+, optional pydantic / pytest)
> - All CLIs run `--help` cleanly even when external deps missing
> - 157 pytest tests passing across 4 Skill modules
> - **No fake data** — buyer names / HS codes / etc. are either real-fetched or explicit mock
> - MIT license
>
> End-to-end demo: research pipeline → JSON → assemble → render → 14 KB self-contained HTML you can email.
>
> Repo: https://github.com/Alexxiang2008/hlzd-b2b-export-skills
>
> Why this matters: B2B industrial products have 3-18 month decision cycles, multi-stakeholder buyers, multi-jurisdictional compliance, and rich trust signals (certifications + specs). Generic marketing skills don't fit. The 4 shipped skills anchor a 21-skill roadmap covering the full B2B export lifecycle.
>
> Feedback welcome — especially from any cross-border trade teams who'd like to see specific skills land first.

---

## 📋 投递清单 (Distribution Checklist)

| 渠道 | 帖子格式 | 最佳时机 | 优先级 |
|---|---|---|---|
| 即刻（中文区） | 中文版 | 工作日上午 | 🔥 P0 |
| LinkedIn（中文） | 中文版 + repo link | 周末 | P1 |
| 知识星球 | 中文版 + 演示截图 | 周末 | P1 |
| Hacker News (Show HN) | English | 周二/周三 美东上午 9-11am | 🔥 P0 |
| Reddit r/ClaudeAI | English | 周二上午 | P1 |
| Reddit r/B2B / r/sales | English | 周二 | P2 |
| IndieHackers | English | 周二 | P1 |
| X / Twitter | EN 一句话 tweet + repo | 周二 | P2 |
| Dev.to | EN 长文（5min read）| 周中 | P2 |

## 🎯 HN 投递专属提示（Hacker News 文化）

- Show HN 标题必须直接告知**做了什么**+ 给谁用
- 第一段必须 hook（数字 / 反差 / 痛点）— 不要"we built"
- 评审者会跳：技术深度 / 代码可读 / 是否真有人在用 / 与现有方案差异点
- 准备好被打脸"为什么不用 LangChain / 为什么不用现成 SaaS"的回复
- **敏感**：HN 反感"声明 AI 完成" / 反感过度营销 / 反感虚假需求。诚实陈述 GitHub 0 结果 + 4 Skills 已可跑演示是真实叙事

## 🔥 回应可能被打脸的点（提前准备）

- **"为啥不用 LangChain / 现成 SaaS？"** → 我们追求 stdlib-only + 单文件能跑，零依赖更适合 Agent Skills 集成
- **"数据真实性？合规靠得牢？"** → README 显著标注"非合规判定 / 制裁名单静态快照 / 真实交易请人工复核"
- **"为什么不直接 fork marketingskills？"** → 不能 fork：他们 47 个 skill 全 B2C 路径，HS 编码 + 海关 + 制裁这三条主轴压根没有
- **"21 Skill 计划是不是噱头？"** → Roadmap 在 docs/ 里写得很详细，前 4 已交付，每 Skill 都有 SKILL.md + tests

---

## ✂️ 立即可贴版本（≤ 280 字符 微推版）

> Just shipped 4 Claude Agent Skills for B2B industrial export — GitHub search for "B2B / industrial export / cross-border trade skill" → 0 results, the niche was completely empty. Repo: https://github.com/Alexxiang2008/hlzd-b2b-export-skills · #AI #B2B #Trade

---

*Crafted for B2B industrial exporters · HLZD Cross-Border AI Platform · 2026*
