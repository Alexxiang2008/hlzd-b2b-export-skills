# HLZD B2B 出海 Skill 集 — 4 渠道安装文档

> 这份文档给两类读者：
> - **HLZD 内部销售** — 用 Claude Code 真实接入
> - **GitHub 用户** — clone 试用

---

## 渠道 1：npx skills（推荐 — 通用）

```bash
# 安装 全部 10 个 Skill
npx skills add Alexxiang2008/hlzd-b2b-export-skills

# 只装某几个
npx skills add Alexxiang2008/hlzd-b2b-export-skills \
    --skill hlzd-inquiry-qualify hlzd-trade-compliance

# 列出已装的 Skills
npx skills ls

# 升级
npx skills update
```

依赖：Node 18+。Skill 装到 `~/.agents/skills/`。

---

## 渠道 2：Claude Code Plugin Market

```bash
# 添加仓库作为 marketplace
/plugin marketplace add Alexxiang2008/hlzd-b2b-export-skills

# 安装指定 Skill
/plugin install hlzd-inquiry-qualify
/plugin install hlzd-trade-compliance
/plugin install hlzd-cold-outreach

# 安装全部
/plugin install --all
```

Skill 装到 `~/.claude/plugins/`。

---

## 渠道 3：Submodule（git-native）

```bash
cd your-project/
git submodule add https://github.com/Alexxiang2008/hlzd-b2b-export-skills.git vendor/hlzd
git submodule update --init --recursive

# 在 .gitmodules 中会新增：
# [submodule "vendor/hlzd"]
#   path = vendor/hlzd
#   url = https://github.com/Alexxiang2008/hlzd-b2b-export-skills.git
```

调用方式：
```python
from vendor.hlzd.skills.hlzd_inquiry_qualify.scripts.inquiry_parser import parse_inquiry
```

---

## 渠道 4：Clone（极简）

```bash
git clone https://github.com/Alexxiang2008/hlzd-b2b-export-skills.git
cd hlzd-b2b-export-skills

# 不需要任何安装！所有 Skill 都是 stdlib + 一两个 pip 包
py -m pytest skills/*/tests/ -q
py skills-demo/run_full_demo.py --all
```

直接 Python 调：
```python
import sys
from pathlib import Path

# 把某个 Skill 的 scripts 目录加进 path
sys.path.insert(0, str(Path("skills/hlzd-inquiry-qualify/scripts")))
import inquiry_parser
result = inquiry_parser.parse_inquiry("your inquiry text here")
```

---

## 安装后验证（5 步）

### 1. 跑测试：所有 Skill 应 100% 通过

```bash
py -m pytest skills/*/tests/ -q
# 期望: 384 passed
```

### 2. 验证 SKILL.md 合规

```bash
py validate_skills.py
# 期望: 10/10 OK
```

### 3. 跑 demo 验证

```bash
py skills-demo/run_full_demo.py --all
# 期望: 3 scenarios 全跑出 trace JSON 到 skills-demo/outputs/
```

### 4. 单独测试一个新 Skill

```bash
# 询盘评估
py skills/hlzd-inquiry-qualify/scripts/inquiry_parser.py \
    --input skills/hlzd-inquiry-qualify/assets/inquiry_samples/01-saudi-rfq.txt \
    --pretty

# 跑合规
echo '{"buyer_name":"Hezbollah","buyer_country":"Lebanon"}' | \
    py skills/hlzd-trade-compliance/scripts/cli.py --stdin
echo $?
# 期望: 2 (BLOCKED)
```

### 5. 整套闭环（10 Skill 串联）

```bash
py skills-demo/run_full_demo.py --scenario scenario-saudi-rfq

# 看 outputs
cat skills-demo/outputs/scenario-saudi-rfq-trace.json | python -m json.tool | head -50
```

---

## 故障排查

| 问题 | 解决 |
|---|---|
| `npx: command not found` | 装 Node 18+: `brew install node` 或 https://nodejs.org |
| `validate_skills.py` 报 SKILL.md 缺失 frontmatter | 检查每 skill/SKILL.md 顶部 `---` 行；`name` 字段必须与目录名一致 |
| 单个 Skill 测试失败 | `cd skills/hlzd-X && py -m pytest tests/ -v` 调试 |
| trade-compliance bridge load failed | 检查 `skills/hlzd-trade-compliance/data/*.csv` 三个文件都在 |
| 客户测问 import 慢 | 默认 5 道 + 65 行数据，应该 < 1 秒；慢 > 3 秒说明 IO 问题 |
| SLN（SDN List）字段缺失 — 客户要求"全量" | v0.1 仅静态 80 行；生产用 v0.2 接 OFAC 实时 CSV API |

---

## 升级

```bash
# 重新安装最新版本
npx skills update
# 或者 git pull
git pull origin main
```

CHANGELOG 见 `VERSIONS.md`。Skill API 字段保持稳定到 v1.0；v1.x 兼容 v0.1.x 输入输出 schema。

---

## 卸载

```bash
npx skills remove alexxiang2008/hlzd-b2b-export-skills
# 或
git submodule deinit -f vendor/hlzd
rm -rf vendor/hlzd .git/modules/vendor/hlzd
```

---

*Crafted for HLZD B2B export · 2026 · see [GitHub](https://github.com/Alexxiang2008/hlzd-b2b-export-skills) for issue tracker*
