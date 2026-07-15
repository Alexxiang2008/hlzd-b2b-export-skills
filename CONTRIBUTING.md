# Contributing to HLZD Cross-Border B2B Skills

感谢愿意贡献！请在动手前通读本指南，避免做无用功。

## 在提交之前

- 读 [AGENTS.md](AGENTS.md) 的命名规范 / frontmatter / 脚本约束
- 读 [docs/出海技能集规划.md](docs/出海技能集规划.md) 看看你的提案是否在 Roadmap 中
- 没有的 Skill 可以提案 → 开 Issue 描述场景 / 输出 / Skill 边界，先讨论再开 PR

## 开发环境

- Python 3.10+（测试在 3.14 上通过）
- pytest（`pip install pytest pytest-cov`）
- 可选：black / ruff / pydantic

## 提出新 Skill：PR 检查清单

- [ ] `name` 与目录名一致、小写 + 连字符、`hlzd-` 前缀
- [ ] `description` ≥ 20 字符，1-1024 字符；含中英文触发词
- [ ] `SKILL.md` ≤ 500 行
- [ ] 含 `When to use` / `When NOT to use` / `How invoked` / `Related Skills` / `Boundaries`
- [ ] 脚本走 CLI `--input` / `--stdin` 双通道
- [ ] 测试覆盖率 ≥ 80%
- [ ] `py validate_skills.py` 0 errors
- [ ] 在 `marketplace.json` 注册新 Skill
- [ ] 在 `VERSIONS.md` 加 changelog 行
- [ ] 在 `README.md` 表加一行

## 改进现有 Skill

- [ ] 改动不破坏 skill 接口（frontmatter `name` / `description` / `version`）
- [ ] 改 frontmatter `description` 也算 minor 升级（bump version + changelog）
- [ ] 同步更新 `VERSIONS.md`
- [ ] 保留向后兼容（如必须破坏接口，请在 Issue 讨论后再做）

## Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: add hlzd-customer-due-diligence skill
fix: tighten media regex to avoid "qualification" false positive
docs: clarify How invoked in hlzd-inquiry-qualify
test: cover Spanish-path in inquiry parser
refactor: extract company-patterns to shared module
chore: bump hlzd-inquiry-qualify to 0.1.1
```

## PR 流程

1. Fork → 创建分支 `feature/hlzd-<skill-name>` 或 `fix/<skill>-<desc>`
2. 写代码 → 本地跑 `py validate_skills.py` + `pytest`
3. push → 开 PR
4. 至少 1 个 reviewer 通过 → 合并

PR 标题参考：`feat(skill): hlzd-customer-due-diligence` 

## 行为准则

- 公开任何客户 / 真实公司 / 真实邮箱 → 必须匿名化
- 禁止硬编码 API Key / 私钥 / 凭证
- 制裁名单仅做粗筛演示，**禁止**在代码里直接 hard-coded 真实制裁实体名单（必须来自 OFAC / EU / UN 公开 API）

## 安全问题

发现漏洞请**不要**开公开 Issue → 直接邮件联系仓库负责人（见 [`CODEOWNERS`](CODEOWNERS)）。我们会 48 小时内响应。

---

*HLZD Cross-Border AI Platform · 2026*
