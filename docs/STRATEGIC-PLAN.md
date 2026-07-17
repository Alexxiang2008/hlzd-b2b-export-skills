# HLZD Skill 战略规划 (v1.4)

> **源文件**：`hlzd-skills-roadmap` (本地 v0.1, 2026-07) 整合入仓库 v1.4。
> **目标**：Claude Code 中能跑通的 B2B 工业品出口全链路 skill 地图。

---

## 一、设计原则

1. **单一 source of truth**：仓库 `Alexxiang2008/hlzd-b2b-export-skills` (v1.4) 是所有实现的 source of truth。
2. **每个 skill 可在 Claude Code 跑通**：SKILL.md frontmatter 合规 + scripts/ 1+ Python + tests/ 1+ pytest + 100% pass。
3. **零外部依赖优先**：stdlib only；网络/AI 依赖作为可选 adapter。
4. **合并优于分叉**：同名 skill 在仓库只存在一个最强实现。

---

## 二、Skill 合并谱系

仓库最终 22 skill。**合并历史**：

| 现仓库名 | 来源 (合并前) | 备注 |
|---|---|---|
| `hlzd-b2b-research` | 本地 HLZD-B2B工业品调研 + ZIP hlzd-b2b-research stub | 仓库为最强实现 |
| `hlzd-data-viz` | ZIP hlzd-d3-viz + 本地 HLZD-D3可视化 | 一致 |
| `hlzd-image-gen` | 本地 HLZD-图片生成 + 仓库 v0.1 product-image-gen + ZIP hlzd-image-gen | 重命名 |
| `hlzd-video-gen` | 本地 HLZD-视频生成 + 仓库 v0.1 product-video-gen + ZIP hlzd-video-gen | 重命名 |
| `hlzd-office-doc` | 本地 HLZD-办公文档 + ZIP hlzd-office-doc | v0.1 纯 stdlib |
| `hlzd-finance-risk` | 仓库 v0.1 + ZIP hlzd-lc-review v0.4 软条款 catalog (v0.1.1) | 增量升级 |
| `hlzd-customer-profile` | 仓库 v0.1 + ZIP hlzd-customer-persona stub | 仓库为最强 |

---

## 三、HLZD 三大 runtime 关系

```
                  Alexxiang2008/hlzd-b2b-export-skills
                       (v1.4 仓库 22 skills)
                            ▲
                            │ source of truth
                            │
       ┌────────────────────┼─────────────────────┐
       │                    │                     │
  Claude Code /         Panmira 平台        本地 Claude
  通用 Agent CLI       (hlzd-trade-            Code / 镜像
  (npx / plugin)        superpowers)         (~/.claude/skills)
  CI: 22/22 ✅           投产 5 + 储备 4
  610 tests              + 4 PROCESS + 1 META
```

**ZIP hlzd-trade-superpowers v0.1.0** 的 17 skill：

- 5 投产（d3-viz / image-gen / video-gen / office-doc / lc-review）→ 仓库镜像/升级
- 4 储备 stub（customer-persona / inquiry-response / shipment / daily-report）→ 仓库已 ship 对应
- 1 META（writing-skill）+ 4 PROCESS（deal-brainstorming/execution/planning/reflection）→ **Panmira workflow 专属**，不上仓库

---

## 四、v1.4 终态 22 Skill 地图

| 类别 | 数 | Skill 列表 |
|---|---|---|
| 入口 | 1 | `hlzd-inquiry-qualify` |
| 调研 | 3 | `hlzd-b2b-research`, `hlzd-data-viz`, (market-intel v0.2 待加) |
| 找买家 | 1 | `hlzd-buyer-finder` |
| 背调 | 2 | `hlzd-customer-due-diligence`, `hlzd-customer-profile` |
| 触达 | 3 | `hlzd-cold-outreach`, `hlzd-followup-sequencer`, `hlzd-rfp-response` |
| 报价 | 3 | `hlzd-solution-match`, `hlzd-quotation-gen`, `hlzd-negotiation-playbook` |
| 合规/物流/财务 | 3 | `hlzd-trade-compliance`, `hlzd-logistics-planner`, `hlzd-finance-risk` |
| 报告 | 2 | `hlzd-market-report`, `hlzd-pipeline-viz` |
| 日常 | 1 | `hlzd-daily-report` |
| 媒体 | 2 | `hlzd-image-gen`, `hlzd-video-gen` |
| 办公 | 1 | `hlzd-office-doc` |
| 知识 | 1 | `hlzd-knowledge-graph` |
| **总** | **22** | |

---

## 五、v0.2 增量路线

| Skill | 内容 | 触发场景 |
|---|---|---|
| `hlzd-market-intel` | 市场情报 dashboard (海关数据/行业报告) | 当前 v0.1 只有 1 file stub，待补 implementation |
| `hlzd-office-doc` v0.2 | DOCX/PDF/Excel/PPTX round-trip + 抬头纸模板渲染 | 需 libreoffice / pandoc，**用户需本地安装二进制** |
| `hlzd-image-gen` v0.2 | Agnes API 实际调用支持 (key 配置 + batch + history UI) | 当前 v0.1 mock-only |
| `hlzd-video-gen` v0.2 | FFmpeg pipeline 实际视频合成 + 字幕烧录 | 当前 v0.1 mock-only |
| `hlzd-finance-risk` v0.4 | 完整 UCP 600 / ISBP 745 / ISP98 / URDG 758 规则库 (v0.4 design 文档) | 当前 v0.1.1 仅含软条款 catalog |
| `hlzd-trade-compliance` v0.2 | 接 OFAC / EU / BIS 实时 API (替代静态 65 行) | 当前 65 行是 v0.1 stub |

---

## 六、SKILL.md frontmatter 强制项（仓库合并后所有 22 个都符合）

```yaml
---
name: hlzd-<skill-name>     # 必须与父目录名完全一致
description: "..."            # 包含中英文触发词 + Use when
license: MIT
metadata:
  author: HLZD
  version: 0.x.x             # semver
  industry: cross-border-b2b
  category: <category>
  triggered_by:
    - 中文触发词 1
    - 英文触发词 1
    - ...
---
```

校验器：`py validate_skills.py`（v0.1 fix 后已 track 到仓库）

---

## 七、测试标准（每个 skill 必须）

| 维度 | 要求 |
|---|---|
| SKILL.md | frontmatter 合规 + 中文+英文触发词 + workflow 描述 |
| scripts/ | 1+ Python 文件，可作为模块被 import |
| tests/ | 1+ pytest 文件 |
| `py -m pytest tests/` | 100% pass |
| `py validate_skills.py` | OK |
| `py -m pytest` (仓库根) | 累计 ≥ 600 tests pass |
| Claude Code 实际运行 | 可作为 Skill tool 调用 |

---

## 八、决策历史

- **v1.0.0 (2026-07-15)**：仓库 10 skills 起步（inquiry-qualify 等）
- **v1.1.0 (2026-07-16)**：+trade-compliance (W8)
- **v1.2.0 (2026-07-16)**：+daily-report / customer-profile / rfp-response / logistics-planner / finance-risk / data-viz / product-image-gen / product-video-gen
- **v1.3.0 (2026-07-16)**：+followup-sequencer / knowledge-graph / pipeline-viz
- **v1.4.0 (TBD)**：product-image-gen → image-gen + product-video-gen → video-gen (重命名) + office-doc 新增 + finance-risk v0.1.1 (软条款 catalog)

---

## 九、清理 (2026-07-17)

- 仓库：97 个无关文件删除 + validate_skills.py 添加 track + .gitignore hardening
- 本地：删除 HLZD 重复 + 1f stub 目录（market-intel 1f / skills-roadmap 已并入 docs/）
- ZIP：仅 reference 用途（不直接 push）
- **总跟踪文件**：315 → **219**（-97 删除 + 1 新 track）

---

*Source of truth: docs/STRATEGIC-PLAN.md (v1.4, 2026-07-17)*
*Repository: https://github.com/Alexxiang2008/hlzd-b2b-export-skills*
