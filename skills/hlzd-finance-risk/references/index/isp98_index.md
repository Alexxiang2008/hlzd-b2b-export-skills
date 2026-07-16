# ISP98 章节索引

> **文件**：`references/rules/ISP98.md`（1152 行，ICC Publication No. 590，1999-01-01 生效）
> **用法**：按 Rule 编号 `Read` 对应行号范围。
> **审单触发**：L/C 类型 = `STANDBY` / `PERFORMANCE_STANDBY` / `ADVANCE_PAYMENT_STANDBY` / `BID_BOND_STANDBY` / `DIRECT_PAY_STANDBY` 时必读。

## 关键条文速查

| Rule | 行号范围 | 主题 | 实务应用 |
|---|---|---|---|
| **1.06** | 187-205 | **Nature of Standbys** | 默示不可撤销 + 独立 + 单据性 + 签发即生效 |
| 1.07 | 207-209 | Independence（独立性）| 不依赖基础交易 |
| 1.09 | 229-289 | Defined Terms（定义）| |
| **1.11** | 389-? | Interpretation | |
| **2.01** | 391-423 | **Undertaking to Honour** | 付款义务 |
| 2.04 | 433-? | Nomination（指定人）| |
| **3.02** | 479-? | Presentation（提示时间）| 排除起始日 |
| **3.06** | ? | **Electronic Presentation** | ISP98 鼓励电子化 |
| **3.08** | ? | **Partial Presentations** | 允许部分提示 + 自动减额 |
| **4.01** | 625-? | **Examination Standard** | **3 个银行工作日**（比 UCP 严）|
| **4.11** | ? | Non-documentary Conditions | 视为未规定 |
| **5.01** | 815-? | **Notice of Refusal** | **单个通知** |
| **5.02** | ? | **Content of Refusal Notice** | **每个不符点列明** |
| **5.03** | ? | **Refusal Time Limit** | 审单 + 1 天 = 4 银行工作日 |
| 6.01 | 893-? | Transferable（可转让）| |
| **6.08** | ? | Assignment of Proceeds（收益权转让确认）| |
| 7.01 | 1051-? | Cancellation（撤销）| |
| 9.01 | 1115-? | Expiry（到期）| 必须含到期日 |

## ISP98 vs UCP 600 关键差异

| 维度 | UCP 600 | ISP98 |
|---|---|---|
| 审单时限 | 5 银行工作日 | **3** 银行工作日 |
| 拒付通知 | 5 银行工作日 | 审单 + 1 天 = 4 天 |
| 交单期 | 21 日历日（装运后） | **不规定**（按需提示）|
| 默示不可撤销 | 否（需明示） | **是**（Rule 1.06(a)）|

## Grep 关键词

```bash
# 例：审单时限
Grep "three banking days" references/rules/ISP98.md

# 例：拒付通知
Grep "single notice" references/rules/ISP98.md

# 例：独立性
Grep "independence" references/rules/ISP98.md

# 例：电子提示
Grep "electronic presentation" references/rules/ISP98.md
```