# ISBP 745 章节索引

> **文件**：`references/rules/ISBP_745.md`（1454 行，ICC Publication No. 745，UCP 600 实务补充）
> **用法**：按段落 A1-A41 / B-K / 章节 1-9 定位 `Read`。
> **审单触发**：L/C 类型 = `COMMERCIAL_LC` 且涉及运输单据时必读。

## 总览

| 段 | 行号 | 主题 | 何时读 |
|---|---|---|---|
| Preliminary | 1-21 | 适用范围声明 | 通用必读 |
| 1. GENERAL PRINCIPLES | 23-243 | A1-A41 一般原则 | 任何审单 |
| 2. DRAFTS & MATURITY | 245-353 | 汇票 / 到期日 | L/C 含汇票时 |
| 3. INVOICES | 355-423 | 发票签发 / 描述 / 分期 | 必读 |
| 4. MULTIMODAL | 425-561 | 多式联运单据 | L/C 含 multimodal 时 |
| 5. BILL OF LADING | 563-713 | 提单 | L/C 含 B/L 时 |
| 6. NON-NEGOTIABLE SWB | 715-857 | 不可转让海运单 | L/C 含 SWB 时 |
| 7. CHARTER PARTY B/L | 859-1005 | 租船合约提单 | L/C 含租船时 |
| 8. AIR TRANSPORT | 1007-1117 | 空运单 | L/C 含空运时 |
| 9. ROAD/RAIL/INLAND | 1119+ | 公路/铁路/内河 | 罕见 |

## A 段（General Principles, A1-A41）必读清单

| 段落 | 主题 | 实务应用 |
|---|---|---|
| A1 | Abbreviations（缩写）| Int'l / Co. / kgs 等通用缩写允许 |
| A2 | Virgules / Commas（斜杠 / 逗号歧义）| "Red/Black/Blue" = 任一或组合 |
| A3-A5 | Certificates / Certifications | 需签字 / 日期规则 |
| A7-A11 | Dates（日期规则）| 装运日 / 提示日 / 顺延 |
| A19 | Originals and Copies（原单据 vs 副本）| 标记 / 副本无需签字 |
| A23 | Signatures（签字）| 手签 / 摹签 / 电子签 |
| A26 | Conflict of Data（数据冲突）| 单据之间 / 与 L/C 冲突 |
| A41 | Non-documentary Conditions（非单据条件）| 视为未规定 |

## Grep 关键词

```bash
# 例：缩写规则
Grep -A 5 "^A1)" references/rules/ISBP_745.md

# 例：日期规则
Grep -A 3 "date of shipment" references/rules/ISBP_745.md

# 例：非单据条件
Grep "non-documentary" references/rules/ISBP_745.md
```