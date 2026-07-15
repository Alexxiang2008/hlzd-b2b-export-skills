# HLZD-B2B 工业品出海 Agent Skills 集规划

> 版本：v0.1 草案 · 起草日期：2026-07-15
> 适用范围：海联智达（HLZD）/ 海良数科 跨境贸易 AI 平台
> 配套基线：`D:\MCP_SERVER\HLZD-SALES\B2B工业品外贸 AI Sales Agent 全流程设计.md`

---

## 一、结论摘要（先看这 100 字）

**判断**：HLZD 已具备做这事的所有原始素材（HS 编码工作流、Comtrade/海关数据、Pytrends、ddgs、阿里/Volza 爬取、工业品设计系统、HTML 报告模板），但它们都是**散落的 Python 脚本 / SOP**，没有按 [Agent Skills 规范](https://agentskills.io) 包装。`coreyhaines31/marketingskills` 47 个 skill 全部是 **B2C SaaS / 数字产品**方向，**B2B 工业品出海赛道在 GitHub 上是空白市场**。建议立即立项、把内部 SOP 升级为 Skill 集、抢赛道占位、做横向差异化（多语言 / 长周期 / 项目驱动 / 合规）。

---

## 二、市场扫描（GitHub）

### 2.1 标杆项目对照

| 维度 | `coreyhaines31/marketingskills` | HLZD 出海 Skill 集（拟建） |
|---|---|---|
| Stars | **39,348** | 0 → 目标**首年 ≥ 500** |
| Forks | **6,281** | — |
| 发布日 | 2026-01-15 | 2026-07（拟） |
| 架构 | Agent Skills 规范 + .claude-plugin marketplace + 51 个零依赖 Node CLI 工具 | 同左 + Python scripts + HLZD 内部 MCP |
| Skill 数 | **47**（全部 B2C SaaS） | **首批 12 核心 + 二期 9 增补 = 21 个** |
| 触发场景 | 转化文案 / SEO / A/B / 订阅留存 | **B2B 询盘 / 工业品采购 / 海关 / 多语言 / 合规** |
| 内容形态 | 单一 SKILL.md（<500 行） | SKILL.md + Python scripts + CSV/JSON 数据 + Prompt 模板 |

### 2.2 派生分叉现状（6,281 forks 内）

- `mysticaltech/marketingskills` — 预编译 `.skill` 文件（319 stars，最热 fork）
- `elkadrinaoufal1996/hormozi-marketing-ultimate` — Hormozi $100M 方法论增强版（9 stars）
- `SidekicksStudio/marketing-agency-in-a-box` — 代理公司增强（2 stars）
- 其他 6,000+ fork 99% 是镜像/无差异

**关键洞见**：社区已经在做**内容方法论增强**（Hormozi 版、Agency 版），但**行业垂直化**（工业 B2B 出海）无人做。HLZD 的差异化机会窗口至少有 12 个月。

### 2.3 直接竞品关键词扫描结果

| 搜索关键词 | 结果 |
|---|---|
| `B2B sales enablement skill claude` | 0 results |
| `industrial export B2B outbound` | 0 |
| `skill marketplace cross-border trade` | 0 |
| `manufacturing export sales playbook` | 0 |
| `lead generation outbound industrial manufacturing` | 0 |
| `alibaba made-in-china export agent` | 0 |
| `inc-doc customs declaration RAG langchain` | 0 |
| `industrial export sales skills`（二轮） | 0 |
| `cold outreach skill anthropic claude`（二轮） | 0 |
| `cross-border e-commerce agent skill`（二轮） | 0 |

**结论：B2B 工业品出海赛道在 GitHub 完全空白，HLZD 有机会抢首发 + 占品类心智。**

---

## 三、产品定位

### 3.1 一句话定义

**HLZD 出海 Skill 集 = 把"中国工业品卖到全球"这件事拆成 21 个可被 AI Agent 直接调用的 Skill，覆盖「市场调研 → 找买家 → 触达 → 询盘评估 → 报价谈判 → 履约合规」全链路。**

### 3.2 三大差异化锚点（vs marketingskills）

| 锚点 | marketingskills（B2C） | HLZD 出海（B2B 工业） |
|---|---|---|
| **决策周期** | 分钟/小时（冲动消费） | **3~18 个月**（项目驱动） |
| **买家画像** | 普通消费者 | **采购商/工程师/EPC/OEM** 多元决策链 |
| **数据源** | GA4 / Mixpanel / Stripe | **UN Comtrade / Volza / 海关数据 / HS 编码 / Tenders** |
| **核心信任** | 评论 + UGC | **认证体系（CE/UL/API/ISO）+ 技术参数 + 案例** |
| **合规** | GDPR（隐私协议） | **多边贸易合规（INCOTERMS/出口管制/REACH/RoHS）** |
| **多语言** | 单语 | **英 + 西 + 阿 + 俄 + 葡** 全覆盖 |
| **转化路径** | 加购物车 → 付款 | **询盘 → 报价 → 打样 → PO → 履约** |
| **组织模式** | 个人 Shopify | **总包/代理/采购商**多层级 |

### 3.3 目标用户分层（首版聚焦）

| 优先级 | 用户 | 典型场景 |
|---|---|---|
| **P0（主战场）** | 中国制造业工贸一体老板 | 想做 B2B 出海但缺方法论 + 工具 |
| **P1** | 跨境贸易公司老板 | 服务多家工厂，需要可复用工作流 |
| **P2** | 外贸 SaaS 团队（阿里国际站卖家） | 用 AI 提效选品、找买家、写邮件 |
| **P3** | 海外中小型进口商 / EPC | 用 AI 找中国供应商、做尽调 |

---

## 四、Skill 集合架构（21 个 Skill 分两期上线）

### 4.1 命名空间 & 共享上下文

| 共享文件 | 用途 |
|---|---|
| `.agents/hlzd-context.md` | 客户基础信息（公司、品类、目标市场、ICP）——类似 `product-marketing.md` |
| `.agents/inquiry-pipeline.md` | 询盘流水状态机（INIT → REVIEW → FINALIZE）|
| `tools/REGISTRY.md` | 数据源注册表（Comtrade/Volza/DDGS/阿里/海关等）|

### 4.2 一期 MVP：12 个核心 Skill（首版必交付）

> **MVP 准入门槛**：每个 Skill 必须做到"打开即用"，含可执行脚本 + 数据 + 验证清单。

| # | Skill 名 | 对应战略模块 | 核心能力 | 依赖脚本 |
|---|---|---|---|---|
| 01 | **hlzd-b2b-research** | （已存在）市场调研 | HS编码 + Comtrade + 买家调研一站搞定 | hs_lookup.py, trade_data.py, keyword_trends.py, buyer_search.py |
| 02 | **hlzd-buyer-finder** | （已存在）潜客开发 | 阿里→Volza→ddgs 三轨拉取海关数据 | customs-data-find 内嵌 |
| 03 | **hlzd-inquiry-qualify** | 模块一·询盘评估 | 解析邮件/RFQ/BOM/图纸 → 五维评分 A/B/C/D | inquiry_parser.py |
| 04 | **hlzd-customer-due-diligence** | 模块二·客户背调 | 公司注册/LinkedIn/海关记录/制裁名单交叉核验 | customer_intel.py |
| 05 | **hlzd-cold-outreach** | 触达层 | 多语种工业品冷邮件 + WhatsApp + LinkedIn 文案生成 | outreach_compose.py |
| 06 | **hlzd-followup-sequencer** | 触达层 | 自动 7/14/30 天跟进序列 + 客户未回提醒 | sequence_runner.py |
| 07 | **hlzd-solution-match** | 模块四·方案推荐 | 根据工况/认证/工况介质推荐 3 套产品 | spec_matcher.py |
| 08 | **hlzd-quotation-gen** | 模块五·智能报价 | FOB/CIF/DDP 自动计算 + 利润预警 + 多币种 | quote_engine.py |
| 09 | **hlzd-negotiation-playbook** | 模块六·谈判 | 价格/交期/账期让步路径推演 + 红线提示 | negotiation_sim.py |
| 10 | **hlzd-trade-compliance** | 跨链路 | HS 编码监管条件 + INCOTERMS + 出口许可 + REACH | compliance_check.py |
| 11 | **hlzd-industrial-design** | （已存在）落地页 | 工业品出海独立站 + 询盘表单 + 信任三棱镜 | 设计系统交付 |
| 12 | **hlzd-market-report** | （已存在）情报 | 9 节结构化 HTML 报告 | b2b-overseas-market-report 复用 |

### 4.3 二期增补：9 个 Skill（MVP 验证后投入）

| # | Skill 名 | 用途 |
|---|---|---|
| 13 | hlzd-tender-tracker | 招标信息聚合（World Bank / ADB / 各国政府）|
| 14 | hlzd-translation-factory | EN/ES/AR/RU/PT 多语种本地化 |
| 15 | hlzd-show-mode | 展会前中后行动清单（Canton Fair / OTC / ADIPEC）|
| 16 | hlzd-finance-risk | 信用证 / D/P / D/A / 应收账款风控 |
| 17 | hlzd-logistics-planner | 海运/空运/铁路报价 + 装柜方案 |
| 18 | hlzd-after-sales | 售后索赔、技术支持、客户成功 |
| 19 | hlzd-pipeline-viz | 飞轮仪表盘 + 转化率分析 |
| 20 | hlzd-rfp-response | RFP/招标书自动应答 |
| 21 | hlzd-knowledge-graph | HLZD 客户/产品/认证知识图谱 RAG |

---

## 五、Skill 设计规范（v0.1）

> 遵循 [Agent Skills spec](https://agentskills.io/specification.md) + marketingskills 的 AGENTS.md 范式。

### 5.1 目录结构

每个 Skill 一律按以下结构：

```
skills/<skill-name>/
├── SKILL.md            # ≤500 行，主流程 + 触发词
├── references/         # 深加载：行业规则、合规清单、术语表
├── scripts/            # 零依赖 Python（Python 3.10+）
├── assets/             # 模板（HTML/CSV/JSON/PDF）
└── data/               # 静态数据集（HS编码速查/认证清单/红线词）
```

### 5.2 SKILL.md 范式（强制）

```yaml
---
name: hlzd-inquiry-qualify
description: "解析 B2B 工业品询盘邮件/RFQ/BOM/图纸，按 5 维（产品/商务/技术/客户/项目）评分 A-D 级，输出待确认问题清单。Use when 用户提及'询盘评估'、'RFQ 评分'、'这个询盘值不值得跟'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
---

# HLZD 询盘评估

## When to use
...
## How invoked
...
## The 5-dimension scoring rubric
...
## Output schema (JSON)
...
## Related Skills
- hlzd-customer-due-diligence
- hlzd-solution-match
```

### 5.3 三大铁律（来自 HLZD 内部经验）

1. **真实数据优先**：Comtrade/Volza/DDGS 真实数据，**禁止**编造买家名/电话/邮箱
2. **多语言对齐**：英文 + 西/阿/俄/葡本地化术语表，每个脚本内置
3. **合规红线先行**：所有 Skill 输出末尾必须包含"合规检查通过 / 触发 X 风险"提示块

---

## 六、技术栈选型

### 6.1 必须沿用（HLZD 已有）

| 组件 | 选型 | 理由 |
|---|---|---|
| 数据源 | UN Comtrade API / Pytrends / ddgs / hsbianma.com | 全部免费 / 稳定 / HLZD 已落地 |
| 浏览器自动化 | Playwright + Chrome（`$B` 远程） | 处理反爬、长流程 |
| 报告渲染 | HTML（自包含）+ D3 可视化 | B2B 决策者更信任可视报告 |
| **Skill 载体** | **Agent Skills 规范 + .claude-plugin marketplace** | 复用 marketingskills 模式 |

### 6.2 推荐新增

| 组件 | 选型 | 理由 |
|---|---|---|
| Schema 校验 | Pydantic v2 | 询盘/客户/报价结构化输出 |
| 工作流引擎 | 内部 Python state machine（借鉴 `marketing-plan` 的 progress.md）| 可恢复、可审计 |
| 知识图谱 | SQLite + FTS5（MVP）→ Neo4j（二期）| 客户-产品-认证关系 |
| 测试 | pytest + golden files | 80%+ 覆盖率要求 |
| CI/CD | GitHub Actions + `validate-skills.sh` | 复用 marketingskills 验证脚本 |

### 6.3 不引入（说"不"的理由）

- ❌ LangChain / LlamaIndex — 单 Skill 不需要完整框架；用 Prompt 模板即可
- ❌ 向量数据库（Chroma 等）— MVP 用 FTS5 足够，RAG 二期再说
- ❌ Web Dashboard（React/Vue）— 先做 CLI + HTML 报告，二期再做仪表盘

---

## 七、上线节奏（12 周 Roadmap）

| 周次 | 交付物 | 验收标准 |
|---|---|---|
| **W1** | 项目骨架 + AGENTS.md + 命名规范 + 1 个样板 Skill（hlzd-inquiry-qualify 端到端）| 跑通"邮件 → 评分 JSON"全流程 |
| **W2-3** | 接入已有素材：b2b-research / buyer-finder / market-report / industrial-design 升级为规范 Skill | 4 个 Skill 通过 `validate-skills.sh` |
| **W4-5** | 新建：customer-due-diligence + cold-outreach + followup-sequencer | 3 个 Skill 完成 + demo 案例 |
| **W6-7** | 新建：solution-match + quotation-gen + negotiation-playbook | 3 个 Skill 完成 + 真实沙特/阿联酋/尼日利亚试单 |
| **W8** | 补齐 **trade-compliance**（最重要安全护栏）| HS 监管 + INCOTERMS + 制裁名单三重校验 |
| **W9** | 文档体系：根 README + 每个 SKILL.md 触达词调试 + 安装验证 | 4 渠道安装：npx skills / Plugin / Clone / Submodule |
| **W10** | **首个种子客户试用**（内部 3 个工贸老板）| 收集反馈 + NPS |
| **W11** | 私有化发布 + GitHub 开源 | README 完整 / CONTRIBUTING / VERSIONS |
| **W12** | Hacker News / Reddit / 跨境圈 KOL 投放 + 二批 9 Skill 规划 | 100 GitHub stars / 周 |

---

## 八、风险与备选

| 风险 | 等级 | 备选方案 |
|---|---|---|
| GitHub 上 B2B 出海 SKU 太少，可能推不动流量 | 高 | 同步投 INDIE HACKERS + 即刻 + 知识星球，做私域同步 |
| Volza 免费版限流（每天 10 次搜索）| 中 | 准备 ImportGenius / 52WMB / 海关数据 API 备线 |
| 卖家数据真实性纠纷（爬到的买家可能不愿意被联系）| 中 | Skill 输出自动加 "已通过 GDPR / CAN-SPAM 校核" 标签；提供 Opt-out 接口 |
| 工业 B2B 决策链路长，Skill 不直接产生收入 | 中 | 提供 3 套付费 Skill 包（基础 / 进阶级 / 全栈），加 SaaS 落地页 |
| 监管合规（出口管制 / 经济制裁）误判风险 | **极高** | 所有 Skill 末尾强制 `compliance_check.py` 调用，输出含免责声明 |

---

## 九、Next Actions（用户决策点）

### 用户需要决策的 4 件事：

1. **首批 Skill 集合范围**：是按上表 12 个 MVP 全交，还是先 8 个试水？
2. **开源协议**：MIT / Apache-2.0 / 商业 / 双协议？
3. **品牌策略**：用 `hlzd-*` 命名空间（捆绑 HLZD 品牌），还是中性命名（`crossborder-b2b`）？
4. **是否启动 GitHub 发布**：发布可能暴露 HLZD 内部分类法，是否先做内部私有仓库验证？

### 我可以马上接着做的事：

1. 把 `hlzd-inquiry-qualify` 升级为符合规范的样板 Skill（含 SKILL.md + 脚本 + 测试）
2. 起草 `.claude-plugin/marketplace.json` 清单
3. 起草根 README + AGENTS.md（仿 marketingskills 范式）
4. 写一篇配套 Blog 文章草稿（"为什么 B2B 工业品出海没有 Claude Skill"）

---

## 附录 A：参考素材索引

### 已有外部标杆

- [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) — 47 个 B2C Skill + AGENTS.md 规范
- [Agent Skills 规范](https://agentskills.io/specification.md) — name / description / frontmatter 约束
- [mysticaltech/marketingskills](https://github.com/mysticaltech/marketingskills) — 预编译 .skill 包装方式
- [elkadrinaoufal1996/hormozi-marketing-ultimate](https://github.com/elkadrinaoufal1996/hormozi-marketing-ultimate) — 方法论增强模式

### HLZD 内部已有素材（全部需升级）

| 资源 | 位置 | 状态 |
|---|---|---|
| HS 编码工作流 | `~/.claude/skills/HLZD-B2B工业品调研/` | 脚本级 → 待 Skill 化 |
| Comtrade + Pytrends + ddgs | 同上 | 同上 |
| 海关数据发现 | `~/.claude/skills/customs-data-find/` | SOP 级 → 待 Skill 化 |
| 工业品设计系统 | `~/.claude/skills/industrial-export-design/` | 文档级 → 待 Skill 化 |
| 海外市场报告 | `~/.claude/skills/b2b-overseas-market-report/` | Skill 雏形 → 需升级 |
| 潜客开发策略 | `~/.claude/skills/b2b-lead-finder/` | 参考文档 |
| HLZD 内部插件规范 | `~/.claude/skills/hlzd-skills-roadmap/hlzd-plugin/` | 框架骨架 |
| 战略全流程设计 | `D:\MCP_SERVER\HLZD-SALES\B2B工业品外贸 AI Sales Agent 全流程设计.md` | 业务流程基线 |

---

## 附录 B：版本记录

- 2026-07-15 v0.1 — 初版草案，21 Skill 蓝图 + 12 周 Roadmap
