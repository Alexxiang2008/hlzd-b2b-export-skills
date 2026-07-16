---
name: hlzd-finance-risk
description: "B2B 信用证 + 备用信用证 + 见索即付保函审单 —— UCP 600 / ISBP 745 / ISP98 / URDG 758 四套规则库自动适配，软条款 + 不符点 + 制裁国 + 银行国别风险 CRITICAL 提示。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: finance
  triggered_by:
    - 信用证审单
    - L/C审单
    - UCP 600
    - ISBP 745
    - ISP98
    - URDG 758
    - 备用信用证
    - 见索即付保函
    - soft clause
    - 软条款
    - 不符点
    - discrepancy
    - 交单
    - letter of credit
    - standby LC
    - demand guarantee
    - 审证
    - 改证
    - DOCDEX
    - 拒付风险
    - LC review
    - guarantee review
    - compliance check
---

# HLZD 信用证审单 v0.3（渐进式披露版）

> **v0.3 重构**：v0.2 的 825 行 SKILL.md 收缩到 ~200 行，全部 ICC 规则原文从 SKILL.md 移出到 `references/rules/*.md`，SKILL.md 只保留**触发 / 工作流 / 适配矩阵 / 检测算法**。Claude 审单时**按需 `Read references/<file>.md` 的对应章节**，不一次性加载全文。

---

## 1. 三套规则库映射（先做这一步）

| L/C 关键词 | L/C 类型 | 适用规则库 | references 入口 |
|---|---|---|---|
| `documentary credit` / `commercial credit` / `sight payment` / `usance` + 含运输单据 | **Commercial LC** | UCP 600 + ISBP 745 | `rules/UCP_600.md` + `rules/ISBP_745.md` |
| `standby` / `performance` / `bid bond` / `advance payment` / `direct pay` / `ISP98` | **Standby LC** | ISP98（推荐）或 UCP 600 fallback | `rules/ISP98.md`（首选）；仅当 L/C 明确排除 ISP98 时退回 UCP 600 |
| `URDG 758` / `demand guarantee` / `counter-guarantee` / `guarantee` | **Demand Guarantee** | URDG 758 | `rules/URDG_758.md` |
| 都不匹配 | **Unknown** | 默认按 Commercial LC + 标注 `UnknownLCTypError` | — |

**关键时限速查**（细节条文按需读 references/）：

| 时限 | UCP 600 | ISP98 | URDG 758 |
|---|---|---|---|
| 审单 | 5 银行工作日 | **3** 银行工作日 | 5 银行工作日 |
| 拒付通知 | 5 银行工作日 | 审单 + 1 天 = 4 天 | — |
| 付款 | — | — | 审单后 + 2 银行工作日（共 7 天） |
| 交单期 | 21 日历日（装运后） | 不规定 | — |
| 到期日 | 必须 | 必须 | 必须（含到期事件） |

---

## 2. 工作流（14 步）

```
输入（L/C PDF / 扫描件 / MT700 SWIFT）
  ↓
[1]  OCR + 字段提取（Claude 直接 Read 文件，PDF/图片均可）
  ↓
[2]  文档类型识别（模板/草稿/已签发）→ scripts/detect_doc_type.py
  ↓       ├─ TEMPLATE → 列出 [Insert XXX] 字段，让用户填写后重提
  ↓       ├─ DRAFT → 提示等待正式版
  ↓       └─ ISSUED → 继续
  ↓
[3]  L/C 类型识别 → scripts/detect_lc_type.py
  ↓
[4]  HLZD 角色识别 → scripts/detect_role.py（受益人/申请人/担保人）
  ↓
[5]  按类型加载 references/ 索引：
  ↓       Commercial → references/index/ucp600_index.md + isbp745_index.md
  ↓       Standby    → references/index/isp98_index.md
  ↓       Guarantee  → references/index/urdg758_index.md
  ↓
[6]  按 Article/Rule 编号 → Read rules/<file>.md 的对应章节（grep 或行号）
  ↓
[7]  软条款扫描 → references/catalogs/soft_clauses_catalog.md（20+ 跨库条款）
  ↓
[8]  不符点检测 → references/catalogs/discrepancies_catalog.md
  ↓
[9]  装期/交单期/有效期协调（按 §1 时限表）
  ↓
[10] 银行国别风险评级（制裁名单 + 历史拒付，CRITICAL=制裁国）
  ↓
[11] 综合风险评级 = 不符点 + 软条款 + 银行风险 加权
  ↓
[12] 改单建议清单 + 谈判话术（references/catalogs/amendment_playbook.md）
  ↓
[13] 关联交叉验证（HLZD-智能报价 贸易术语 / HLZD-客户画像 国别风险）
  ↓
[14] 飞书卡片返回 + 审单报告 markdown（HLZD 抬头纸由 HLZD-办公文档 skill 生成 PDF）
```

---

## 3. 三个检测算法（伪代码，详细 Python 见 scripts/）

### 3.1 L/C 类型检测（`scripts/detect_lc_type.py`）

```python
def detect_lc_type(text: str) -> str:
    t = text.upper()
    # 优先级 1: URDG 758
    if "URDG 758" in t or "DEMAND GUARANTEE" in t or "COUNTER-GUARANTEE" in t:
        return "DEMAND_GUARANTEE"
    # 优先级 2: ISP98
    if "STANDBY" in t or "ISP98" in t:
        for kw, lc_type in [
            ("PERFORMANCE", "PERFORMANCE_STANDBY"),
            ("ADVANCE PAYMENT", "ADVANCE_PAYMENT_STANDBY"),
            ("BID BOND", "BID_BOND_STANDBY"),
            ("DIRECT PAY", "DIRECT_PAY_STANDBY"),
        ]:
            if kw in t:
                return lc_type
        return "STANDBY"
    # 优先级 3: UCP 600 / 默认
    if "UCP 600" in t or "UCP600" in t or "DOCUMENTARY CREDIT" in t:
        return "COMMERCIAL_LC"
    return "UNKNOWN"
```

### 3.2 文档状态检测（`scripts/detect_doc_type.py`）

```python
import re
def detect_doc_type(text: str) -> str:
    t = text.lower()
    # 模板: 3+ 个 [Insert XXX] 占位符
    placeholders = len(re.findall(r"\[insert [a-z\s]+\]", t))
    if placeholders >= 3:
        return "TEMPLATE"
    # 草稿: 含 draft / watermark / sample
    if any(k in t for k in ("draft", "watermark", "sample")):
        return "DRAFT"
    return "ISSUED"
```

### 3.3 HLZD 角色检测（`scripts/detect_role.py`）

```python
def detect_role(text: str, hlzd_name: str) -> str:
    """根据 L/C 文本和 HLZD 公司名出现的位置判断角色"""
    upper = text.upper()
    hlzd_upper = hlzd_name.upper()
    for role, keyword in [("APPLICANT", "APPLICANT"),
                          ("BENEFICIARY", "BENEFICIARY"),
                          ("GUARANTOR", "GUARANTOR")]:
        idx = upper.find(keyword)
        if idx >= 0:
            window = upper[idx: idx + 300]
            if hlzd_upper in window:
                return role
    return "UNKNOWN"
```

完整实现见 `scripts/`。所有脚本遵循 `_ensure_utf8_stdio()` Windows 兼容模式（CLAUDE.md §1）。

---

## 4. 软条款 / 不符点 / 改单话术（按需读 references/catalogs/）

| 目录 | 何时读 | 体积 |
|---|---|---|
| `references/catalogs/soft_clauses_catalog.md` | 步骤 [7] | 跨 UCP/ISP/URDG 20+ 条 |
| `references/catalogs/discrepancies_catalog.md` | 步骤 [8] | UCP 15 类 + ISP 4 类 + URDG 3 类 |
| `references/catalogs/amendment_playbook.md` | 步骤 [12] | 改单建议 + 谈判话术模板 |

**不要把 catalogs 一次性 Read 全文**——先用 `Grep` 关键词定位，再用 `Read` 读目标行号。

---

## 5. 规则文件全文（**只在条文引用时 Read**）

| 规则 | 路径 | 何时 Read | 行数 |
|---|---|---|---|
| UCP 600 | `references/rules/UCP_600.md` | 步骤 [6] 涉及 Article 14 / 16 / 17 / 18 / 19-25 / 28 / 30 时 | 868 |
| ISBP 745 | `references/rules/ISBP_745.md` | 步骤 [6] 涉及运输单据（Sec 4-9）或发票（Sec 3）或一般原则（Sec 1）时 | 1454 |
| ISP98 | `references/rules/ISP98.md` | 步骤 [6] 涉及 Rule 1.06 / 4.01 / 5.01-5.03 / 3.06 时 | 1152 |
| URDG 758 | `references/rules/URDG_758.md` | 步骤 [6] 涉及 Article 4-7 / 12 / 15 / 17 / 24-25 / 31-35 时 | 510 |

**索引文件**（先用索引定位章节，再按行号 Read）：
- `references/index/ucp600_index.md`
- `references/index/isbp745_index.md`
- `references/index/isp98_index.md`
- `references/index/urdg758_index.md`

---

## 6. 错误地图

| 异常 | 严重度 | 处理 |
|---|---|---|
| `TemplateDetected` | INFO | 列出 [Insert XXX] 字段，让用户补齐 |
| `DraftDetected` | INFO | 提示等待正式版 |
| `UnknownLCTypError` | MEDIUM | 默认按 Commercial + 提示确认 |
| `RoleMismatchError` | HIGH | HLZD 角色与 L/C 不匹配 → 人工确认 |
| `ExpiredLCError` | CRITICAL | L/C 已过期，无法交单 |
| `PresentationPeriodTooShortError` | HIGH | 交单期 < 14 天 → 要求改证延长 |
| `SanctionedCountryError` | CRITICAL | 制裁国银行 → 法务通知，**禁止交单** |
| `UnknownBankError` | MEDIUM | 银行不在 HLZD 历史库 → 提示人工核实 |
| `InconsistentQuoteError` | MEDIUM | L/C 字段与 HLZD-智能报价 冲突 → 高亮 |
| `UnknownSoftClauseError` | LOW | 疑似软条款（不在已收录库）→ 人工确认 |

---

## 7. 协同串联

**上游（被谁触发）**：
- HLZD-智能报价：客户选 L/C 付款 → 自动调本 skill 预审 L/C 模板
- HLZD-询盘响应：客户提到 L/C → 自动加载本 skill
- HLZD-物流装箱：涉及担保/保函（L/G）→ 自动调本 skill

**下游（触发谁）**：
- 拒付风险高 → 自动调 HLZD-客户画像 更新客户风险等级
- 审单完成 → 自动调 HLZD-email-group 起草 L/C 接受通知
- 改单建议 → 自动调 HLZD-智能报价 生成修改后报价

**被动提醒**：
- 装期前 7 天 / 交单期前 3 天 / 有效期前 14 天 / 备用 L/C 修订前 7 天 / 保函到期前 30 天

---

## 8. 性能目标（p99）

| 路径 | 目标 | 预估 |
|---|---|---|
| L/C 类型识别 | < 0.5s | 0.1s |
| 文档类型识别 | < 0.5s | 0.1s |
| 角色识别 | < 0.5s | 0.1s |
| 规则条文引用（grep + Read） | < 2s | 0.5-1s |
| 软条款识别 | < 1s | 0.3-0.8s |
| 不符点检测 | < 2s | 1-1.5s |
| 总耗时（含 OCR） | < 30s | 15-25s |

---

## 9. 安全与合规

1. **不复述 ICC 规则原文**——只引用 Article/Rule/Paragraph 编号 + 实务提示
2. 制裁合规——CRITICAL 风险国家自动阻止 + 法务通知
3. 审计日志——所有审单记录保存 5 年
4. 银行账号保密——只显示后 4 位
5. 反担保隔离——仅 HLZD 财务可见

---

## 10. 已知限制 + 路线图

| 限制 | 计划 |
|---|---|
| OCR 框架设计，无独立 OCR 服务（依赖 Claude Read） | v0.3.1 接 PaddleOCR |
| HLZD 内部实务资料基于 INCOTERMS 2000 | v0.4 升级到 INCOTERMS 2020 |
| 无 SWIFT MT700 自动解析 | v0.4 |
| 无实时制裁名单 API | v0.4（OFAC/EU/UN） |

---

## 11. 部署

```bash
# 打包（保留中文目录名 + Windows 兼容）
tar -czf hlzd-lc-review-v0.3.tar.gz HLZD-信用证审单/

# 部署到 Panmira
tar -xzf hlzd-lc-review-v0.3.tar.gz -C ~/.claude/skills/
mb skills install hlzd-lc-review 青囊

# Windows Junction（中文目录 + 英文别名）
mklink /J C:\Users\13864\.claude\skills\hlzd-lc-review C:\Users\13864\.claude\skills\HLZD-信用证审单
```

---

**v0.3 vs v0.2 升级对比**：

| 维度 | v0.2 | v0.3 |
|---|---|---|
| SKILL.md 长度 | 825 行 / 32KB | **~200 行 / ~7KB** |
| ICC 规则原文位置 | 引用编号在 SKILL.md | **沉到 references/rules/*.md**，按需 Read |
| 索引 | 无 | **references/index/*.md 4 个**（grep 友好） |
| 检测算法 | 伪代码 + 设计稿 | **scripts/*.py 5 个**，可独立跑 |
| 软条款/不符点 | 内嵌 | **references/catalogs/*.md**，Grep 定位 |
| 触发加载量 | 全文一次性 | **触发时 ~7KB + 按需 Read 5-15KB 章节** |

---

**END of HLZD-信用证审单 v0.3 SKILL.md**