# AGENTS.md

> 仓库：**HLZD / Cross-Border B2B Industrial Export Agent Skills**
>
> 范围：所有 AI Agent 在本仓库内工作的指南。
>
> 遵循 [Agent Skills 规范](https://agentskills.io/specification.md) 与 `coreyhaines31/marketingskills` 的范式，并按 **B2B 工业品出海**场景做了业务层定制。

---

## 仓库概览

```
Alexxiang2008/hlzd-b2b-export-skills/
├── .claude-plugin/
│   └── marketplace.json            # Claude Code plugin marketplace 清单
├── skills/
│   └── hlzd-<skill-name>/
│       ├── SKILL.md                # 主入口，≤500 行
│       ├── references/             # 深加载：行业规则、合规清单、术语表
│       ├── scripts/                # 零依赖 Python 3.10+ 脚本（pytest 测试同目录）
│       ├── assets/                 # 模板 + 样本数据
│       └── data/                   # 静态数据集（HS / 认证 / 红线词）
├── docs/
│   └── 出海技能集规划.md            # 战略层 + Skill 集合蓝图 + 12 周 Roadmap
├── README.md
├── AGENTS.md                         # ← 本文件
├── CONTRIBUTING.md                   # PR 流程
├── LICENSE                           # MIT
└── VERSIONS.md                       # 版本与变更日志
```

---

## 命名规范（强制）

### Skill 命名

- 必以 `hlzd-` 前缀（绑定 HLZD 品牌 + 与社区 fork 区分）
- 1-64 字符
- 仅小写字母、数字、连字符
- 不可 `-` 开头 / 结尾 / 连续
- 必须与父目录名完全一致

**有效**：`hlzd-inquiry-qualify`, `hlzd-customer-due-diligence`, `hlzd-cold-outreach`
**无效**：`Inquiry-Qualify`, `-hlzd-xxx`, `hlzd--xxx`, `hlzd_xxx`

### 命名空间建议

| 主题 | 推荐名 |
|---|---|
| 调研 / 情报 | `hlzd-b2b-research`, `hlzd-market-report`, `hlzd-buyer-finder` |
| 销售自动化 | `hlzd-inquiry-qualify`, `hlzd-solution-match`, `hlzd-quotation-gen`, `hlzd-negotiation-playbook` |
| 触达 | `hlzd-cold-outreach`, `hlzd-followup-sequencer` |
| 客户 / 风险 | `hlzd-customer-due-diligence`, `hlzd-trade-compliance`, `hlzd-finance-risk` |
| 履约 | `hlzd-logistics-planner`, `hlzd-after-sales`, `hlzd-rfp-response` |
| 设计 / 内容 | `hlzd-industrial-design`, `hlzd-translation-factory` |
| 内部 / 数据 | `hlzd-knowledge-graph`, `hlzd-pipeline-viz` |

---

## Skill Frontmatter（必填）

每个 `SKILL.md` 文件顶部必须有：

```yaml
---
name: hlzd-<skill-name>
description: "<一句定义> + Use when <触发词，含中英文>。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: <category>
  triggered_by:
    - <中文触发词>
    - <English trigger>
---
```

| 字段 | 必填 | 约束 |
|---|---|---|
| `name` | ✅ | 与目录名一致；小写字母 / 数字 / 连字符；1-64 字符 |
| `description` | ✅ | 1-1024 字符；含触发短语；mention Related Skills |
| `license` | — | 默认 MIT |
| `metadata` | — | 推荐 `author`, `version`, `industry`, `category` |

---

## 目录结构（每个 Skill 必须遵守）

```
skills/hlzd-<skill-name>/
├── SKILL.md            # 必填，≤500 行
├── references/         # 可选：行业规则 / 合规清单 / 术语表
├── scripts/            # 可选：Python 3.10+（零依赖或最少依赖）
├── assets/             # 可选：模板 / 样本 / HTML 报告骨架
└── data/               # 可选：静态数据集（HS 编码 / 认证 / 红线词）
```

---

## SKILL.md 写作风格

### 结构

- 主入口 ≤ **500 行**（细节放 references/）
- H2 章节标题用 `##`、H3 用 `###`
- 多用 bullet / numbered list
- 段落 2-4 句

### 语气

- 第二人称（"You are ..."）
- 直白教学，避免废话
- 专业但可读

### 必含章节

| 章节 | 说明 |
|---|---|
| YAML frontmatter | 触发词 + 版本 + 元数据 |
| When to use | 何时调用 |
| When NOT to use | 不调用情况 |
| How this skill is invoked | 调用方式 / CLI 形式 |
| The main methodology | 工作流 / 评分 / 决策树 |
| Output schema | JSON shape 或可视化结构 |
| Related Skills | 依赖图 + 上下游 |
| Boundaries & Limitations | 必须明示**不**做什么 |
| Versioning | 自记录版本 |

---

## Scripts 规范

### 约束

- **零依赖首选**：只允许 Python 3.10+ 标准库
- 允许可选：`pydantic>=2.6`、`pytest>=8.0`
- 不允许引入：**langchain**、**openai sdk**（那是上层 Agent 的事）
- CLI 必须支持 `--input <file>` / `--stdin` 双通道
- 输出 JSON to stdout（CRM / downstream 友好）
- 中文输出：`sys.stdout` UTF-8-safe（Windows 上默认 GBK → 用 `ensure_ascii=False`）

### 每个脚本必须配一个 `test_<name>.py`

- 同目录 `tests/` 或同目录
- pytest 风格
- 最低 **80% 行覆盖**
- 包含 happy / sad / edge 三种用例

---

## 验证脚本

仓库根放：

```python
#!/usr/bin/env python3
"""validate_skills.py — 检查所有 SKILL.md 是否符合 spec。"""
import re
import sys
from pathlib import Path

def validate_skill(skill_md: Path) -> list[str]:
    errors = []
    fm_match = re.match(r"^---\s*\n(.*?)\n---", skill_md.read_text(encoding="utf-8"), re.DOTALL)
    if not fm_match:
        return [f"{skill_md}: missing YAML frontmatter"]
    fm = fm_match.group(1)

    # name
    name_m = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
    if not name_m:
        errors.append(f"{skill_md}: missing name")
    else:
        name = name_m.group(1)
        dir_name = skill_md.parent.name
        if name != dir_name:
            errors.append(f"{skill_md}: name ({name}) != dir ({dir_name})")
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            errors.append(f"{skill_md}: name {name!r} invalid format (must be lowercase alphanumeric + hyphens)")
        if len(name) > 64:
            errors.append(f"{skill_md}: name too long ({len(name)} > 64)")

    # description
    desc_m = re.search(r"^description:\s*(.+)", fm, re.MULTILINE)
    if not desc_m:
        errors.append(f"{skill_md}: missing description")
    elif len(desc_m.group(1).strip()) < 20:
        errors.append(f"{skill_md}: description too short (<20 chars)")
    elif len(desc_m.group(1).strip()) > 1024:
        errors.append(f"{skill_md}: description too long (>1024 chars)")

    # size
    line_count = len(skill_md.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        errors.append(f"{skill_md}: SKILL.md too long ({line_count} > 500 lines)")

    return errors


def main() -> int:
    root = Path("skills")
    errors = []
    if not root.exists():
        print("no skills/ directory", file=sys.stderr)
        return 1
    for skill_md in root.glob("*/SKILL.md"):
        errors.extend(validate_skill(skill_md))

    if errors:
        for e in errors:
            print(f"ERROR  {e}", file=sys.stderr)
        return 1
    print(f"OK  validated {len(list(root.glob('*/SKILL.md')))} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

运行：

```bash
py validate_skills.py
```

---

## 版本规则

两层版本：

### 仓库级（在 `marketplace.json` 的 `metadata.version`）

- x = 重大不兼容 / 全局重构
- y = 新增 Skill
- z = 仅修复 / 改进现有内容（即便改动很大也不算 y）

### Skill 级（在 SKILL.md frontmatter `metadata.version`）

- 与仓库级独立
- 用户升级脚本对比 VERSIONS.md 检测
- 必填，建议 bump 在每个合并 PR 中做

---

## 如何新增一个 Skill

1. 在 `skills/` 下创建 `hlzd-<name>/`
2. 写 `SKILL.md` （含 frontmatter + When to use + How invoked + Related Skills）
3. 写 `scripts/<cli>.py` （CLI + 0 外部依赖）
4. 写 `tests/test_<cli>.py` （≥ 80% 覆盖）
5. 跑 `py validate_skills.py` 与 `py -m pytest skills/<name>/scripts/`
6. 在 `marketplace.json` 注册
7. 在 `VERSIONS.md` 加 changelog 行
8. 在根 `README.md` 「当前已发布 Skills」表加一行
9. 提交 PR

---

## 致谢 / 致敬

- `coreyhaines31/marketingskills` — Skills 规范参考与文档范式
- Agent Skills 官方规范（[agentskills.io](https://agentskills.io/)）
- HLZD 内部已有素材：`~/.claude/skills/HLZD-B2B工业品调研/`、`industrial-export-design/`、`b2b-overseas-market-report/`、`customs-data-find/`

---

*HLZD Cross-Border AI Platform · 2026*
