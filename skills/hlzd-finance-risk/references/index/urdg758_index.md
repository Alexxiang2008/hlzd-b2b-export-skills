# URDG 758 章节索引

> **文件**：`references/rules/URDG_758.md`（510 行，ICC Publication No. 758，2010-07-01 生效）
> **用法**：按 Article 编号 `Read` 对应行号范围。
> **审单触发**：L/C 类型 = `DEMAND_GUARANTEE` / `COUNTER_GUARANTEE` 时必读。

## 关键条文速查

| Article | 行号 | 主题 | 实务应用 |
|---|---|---|---|
| **1** | 3-13 | **Application of URDG** | 明确引用方适用；2010-07-01 起未注明版本默认 URDG 758 |
| 2 | 15-75 | Definitions | Applicant / Beneficiary / Guarantor / Counter-guarantor 等定义 |
| **4** | 101-109 | **Issuance & Effectiveness** | 保函**离开担保人控制 = 已签发**；默示不可撤销 |
| **5** | 111-117 | **Independence** | 保函独立于基础交易 |
| **6** | 119-123 | Document Examination | 只审单据 |
| **7** | 125-129 | Non-documentary Conditions | 视为未规定 |
| 8 | 131-159 | Content of Instructions（内容要求）| 申请 / 受益 / 金额 / 到期 / 索款条件等 |
| **12** | 205-213 | **Payment Time** | 审单 5 天 + 付款 2 天 = 7 银行工作日 |
| **15** | 247-271 | **Demand & Supporting Statement** | **必须附 supporting statement**；15(a) "due performance" / 15(b) "defaulted" |
| 16 | 273-277 | Refusal of Payment | |
| **17** | 279-? | **Fraud Exception** | 受益人明显欺诈时担保人可拒付 |
| 18 | ? | Court Injunction（法院禁令）| |
| 19 | ? | Force Majeure | |
| 20-23 | ? | Assignment / Transfer | |
| **24-25** | 399-421 | **Expiry** | 到期日 **+ 到期事件**（URDG 758 引入新概念） |
| 27-30 | 437-455 | Charges / Applicable Law / Jurisdiction | |
| **31-35** | 457-505 | **Counter-Guarantee** | 反担保规则 |

## URDG 758 vs UCP 600 vs ISP98 关键时限

| 时限 | URDG 758 | UCP 600 | ISP98 |
|---|---|---|---|
| 审单 | 5 银行工作日 | 5 银行工作日 | 3 银行工作日 |
| 付款 | 审单 + 2 = 7 银行工作日 | — | — |
| 拒付通知 | — | 5 银行工作日 | 4 银行工作日 |

## Grep 关键词

```bash
# 例：索款 + supporting statement
Grep "supporting statement" references/rules/URDG_758.md

# 例：欺诈例外
Grep "fraud" references/rules/URDG_758.md

# 例：到期事件
Grep "expiry event" references/rules/URDG_758.md

# 例：独立性
Grep "independence" references/rules/URDG_758.md
```