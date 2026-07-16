# HLZD-B2B 工业品出海 Agent Skill 集

> Cross-Border B2B Industrial Export Agent Skills for Claude / Codex / Cursor / Windsurf.
>
> 由 [海联智达 HLZD](https://hlzd.example.com) 与 [海良数科](https://hlzd.example.com) 团队开发。
>
> 配套战略文档：[docs/出海技能集规划.md](docs/出海技能集规划.md) ·
> 业务规划：[B2B工业品外贸 AI Sales Agent 全流程设计.md](B2B工业品外贸 AI Sales Agent 全流程设计.md)

---

## 这是什么

一组 **Agent Skill** —— 把"中国工业品卖到全球"这件事拆成 21 个可被 AI Agent 直接调用的 Skill，覆盖「市场调研 → 找买家 → 触达 → 询盘评估 → 报价谈判 → 履约合规」全链路。

| 维度 | 同行（`coreyhaines31/marketingskills`） | HLZD 出海（这里） |
|---|---|---|
| 决策周期 | 分钟/小时（冲动消费） | **3~18 个月**（项目驱动） |
| 买家画像 | 普通消费者 | **采购商/工程师/EPC/OEM** |
| 核心数据源 | GA4 / Mixpanel / Stripe | **UN Comtrade / Volza / HS / Tenders** |
| 信任支柱 | 评论 + UGC | **认证体系 + 技术参数 + 案例** |
| 合规 | GDPR（隐私协议） | **多边贸易合规 + 制裁名单 + 出口管制** |
| 转化路径 | 加购物车 → 付款 | **询盘 → 报价 → 打样 → PO → 履约** |

> GitHub 上 B2B 工业品出海赛道**完全空白**（多关键词搜索 0 结果），HLZD 立志抢赛道首发。

---

## 当前已发布 Skills

| # | Skill | Status | 说明 |
|---|---|---|---|
| 01 | `hlzd-inquiry-qualify` | **v0.1.0** ✅ | 询盘评估：5 维评分 + 多语种抽取 + 合规粗筛 |
| 02 | `hlzd-b2b-research` | **v0.1.0** ✅ | B2B 海外调研：HS + Comtrade + Trends + 买家 + 招标 4 步 pipeline |
| 03 | `hlzd-buyer-finder` | **v0.1.0** ✅ | 海外买家挖掘：阿里 + Volza + 公开目录 3 链路 |
| 04 | `hlzd-market-report` | **v0.1.0** ✅ | 9 节 HTML + 8 节 Markdown 报告生成（Voice Contract 强制）|
| 05 | `hlzd-customer-due-diligence` | **v0.1.0** ✅ | 客户背调：5 维评分 + OFAC SDN + 制裁 + dual-use 粗筛 |
| 06 | `hlzd-cold-outreach` | **v0.1.0** ✅ | 邮件触达：6 类模板 × 双语 + Day 7/14 跟进 |
| 07 | `hlzd-solution-match` | **v0.1.0** ✅ | 方案匹配：5 维评分 + 3 套推荐 (best/alt/cost)|
| 08 | `hlzd-quotation-gen` | **v0.1.0** ✅ | 自动报价：FOB/CIF/DDP 3 套 + 利润健康 + 账期建议 |
| 09 | `hlzd-negotiation-playbook` | **v0.1.0** ✅ | 让步推演：3 轮 × 3 维 + 红线 + 决策路由 |
| 10 | `hlzd-trade-compliance` | **v0.1.0** ✅ | 5 道检查 + 三态路由 + 审计 trail（OFAC + EU + BIS + 国别 + ECCN）|
| 11 | `hlzd-finance-risk` | **v0.1.0** ✅ | B2B L/C + 备用 L/C + 见索即付保函审单，UCP 600 / ISBP 745 / ISP98 / URDG 758 自动适配。 |

闭环演示 — 调研 → 买家 → 背调 → 邮件 → 方案 → 报价 → 让步 → 合规拦截。共 10 / 21 Skill。

---

## 快速开始

### 安装（Claude Code）

```bash
# 1. 添加 marketplace
/plugin marketplace add Alexxiang2008/hlzd-b2b-export-skills

# 2. 安装 inquiry-qualify
/plugin install hlzd-inquiry-qualify
```

### 安装（npx skills — 通用）

```bash
npx skills add Alexxiang2008/hlzd-b2b-export-skills --skill hlzd-inquiry-qualify
```

### 克隆到本地

```bash
git clone https://github.com/Alexxiang2008/hlzd-b2b-export-skills.git
cp -r cross-border-b2b-skills/skills/* .agents/skills/
```

---

## 快速演示：评分一封沙特 OCTG 询盘

```bash
cd skills/hlzd-inquiry-qualify
py scripts/inquiry_parser.py --input assets/inquiry_samples/01-saudi-rfq.txt --pretty
```

输出（截选）：

```json
{
  "detected_language": "en",
  "extracted": {
    "product": {
      "name": "OCTG",
      "specifications": ["NACE MR0175", "L80", "5/8 inch"],
      "quantity": "5000 meters",
      "hs_code_suggestion": "730429"
    },
    "customer": {
      "company_name": "Saudi Aramco Trading Co",
      "country": "Saudi Arabia"
    }
  },
  "scoring": { "total": 85, "grade": "B" },
  "compliance_check": { "two_use_items": true, "passed": true },
  "recommended_next_skill": "hlzd-customer-due-diligence"
}
```

更多样本（噪音 / 西班牙 / 欺诈）见 `skills/hlzd-inquiry-qualify/assets/inquiry_samples/`。

---

## 5 分钟跑全套 demo

仓库自带 3 个场景可立即演示 9 Skill 全链路行为：

```bash
git clone https://github.com/Alexxiang2008/hlzd-b2b-export-skills.git
cd hlzd-b2b-export-skills
py -m pytest skills/*/tests/ -q          # 验证：336 tests
py skills-demo/run_full_demo.py --all     # 跑 3 个场景
```

3 个场景覆盖典型路径：

| Scenario | 路径 | 学到什么 |
|---|---|---|
| `scenario-saudi-rfq` | 真询盘 → 4 buyers → **Hezbollah 触发 halt** → 报价 / 让步 skip | 合规护栏 |
| `scenario-latam-solar` | 真询盘 → 3 buyers → 邮件 → **PV-MODULE-450W-MONO** → FOB $534K margin 15% → **accept_round_3** | 完整 happy path |
| `scenario-fraud-blocked` | 假询盘 → **Grade D total=20** | 自动淘汰 |

详见 [docs/demo-runbook.md](docs/demo-runbook.md)。每个 scenario 完整 trace 落到 `skills-demo/outputs/`。

---

## 路线图

| 周次 | 交付 |
|---|---|
| **W1** | ✅ 样板 Skill：hlzd-inquiry-qualify（已完成） |
| **W2-3** | ✅ 接入已有素材：b2b-research / buyer-finder / market-report |
| **W4-5** | ✅ customer-due-diligence + cold-outreach（touch 链路完工）|
| **W6-7** | ✅ solution-match + quotation-gen + negotiation-playbook（**报价引擎完工**）|
| **W8** | ✅ trade-compliance（合规护栏：**5 道检查 + 三态路由 + 审计 trail**）|
| W9 | 完整文档 + 4 渠道安装验证 |
| W10 | 内部种子客户试跑 |
| W11 | GitHub 私有发布 + 公开提交 |

---

## 贡献

所有 Skill 都欢迎 PR。请先读 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [AGENTS.md](AGENTS.md)，遵守命名规范与 frontmatter约束。

## 安装

[docs/install.md](docs/install.md) — 4 渠道详细命令：npx skills / Plugin / Submodule / Clone。

---

## 安全与免责声明

- 本 Skill 提供**第一道粗筛**，不替代专业贸易合规官。
- 制裁名单为静态快照（每季度更新）。
- 真实交易请人工复核工商 / 海关 / 银行渠道。

---

## 协议

[MIT](LICENSE) — 自由使用、修改、商用。

---

*Crafted for B2B industrial exporters · HLZD 2026.*
