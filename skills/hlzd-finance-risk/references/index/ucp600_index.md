# UCP 600 章节索引

> **文件**：`references/rules/UCP_600.md`（868 行，ICC Publication No. 600，2007-07-01 生效）
> **用法**：审单时按 Article 编号 `Read` 对应行号范围，**不要全文 Read**。
> **审单触发**：L/C 类型 = `COMMERCIAL_LC` 时加载本索引。

## 关键条文速查（必读）

| Article | 行号范围 | 主题 | 实务应用 |
|---|---|---|---|
| 2 | 87-128 | Definitions（定义）| Honour / Complying Presentation 等 14 个定义 |
| 4 | 157-165 | Credits v. Contracts（信用证 vs 合同）| 独立性原则 |
| 6 | 173-189 | Availability（可用性）| by sight payment / deferred payment / acceptance / negotiation |
| 7 | 191-209 | Issuing Bank Undertaking（开证行义务）| 不可撤销 + 独立 + 自负风险 |
| 8 | 211-235 | Confirming Bank Undertaking（保兑行义务）| |
| 14 | 307-333 | **Standard for Examination of Documents** | 审单标准：合理审慎 + 5 银行工作日 + 单据表面一致性 |
| 15 | 335-343 | Complying Presentation（相符交单）| |
| 16 | 345-377 | **Discrepant Documents, Waiver and Notice** | 拒付通知规则：5 天 + 一次性通知 + 列出每个不符点 |
| 17 | 379-397 | Originals and Copies（原单据 vs 副本）| |
| 18 | 399-415 | Commercial Invoice（商业发票）| 货物描述与 L/C 一致 |
| 19 | 417-461 | Transport Document（运输单据 — 一般）| |
| 20 | 463-507 | **Bill of Lading** | 装船批注 / 转运规则 |
| 21 | 509-553 | Non-Negotiable Sea Waybill（不可转让海运单）| |
| 22 | 555-587 | Charter Party B/L（租船合约提单）| |
| 23 | 589-623 | Air Transport Document（空运单）| |
| 24 | 625-663 | Road / Rail / Inland Waterway（公路/铁路/内河运输）| |
| 25 | 665-677 | Courier / Post Receipt（快递/邮包收据）| |
| 26 | 679-687 | On Deck, "Stowed", "Shipped on Board" | 装船批注 |
| 27 | 689-693 | Clean Transport Document（清洁运输单据）| |
| 28 | 695-729 | **Insurance Document and Coverage** | 保险单 / 险种 / 比例 |
| 30 | 739-747 | **Tolerance** | 数量 / 金额 ±10% 容差 |
| 31 | 749-759 | Partial Drawings or Shipments（分批）| |
| 32 | 761-765 | Instalment Drawings or Shipments（分期）| |
| 33 | 767-771 | Hours of Presentation（交单时间）| |
| 35 | 779-787 | English Language / Single Bank（语言/单家银行）| |
| 36 | 789-795 | Force Majeure（不可抗力）| |
| 37 | 797-811 | Disclaimer on Effectiveness of Documents（免责）| |
| 38 | 813-863 | Transferable Credits（可转让信用证）| |
| 39 | 865-868 | Assignment of Proceeds（收益权转让）| |

## 必读组合（按不符点类型）

| 不符点类型 | 必读 Article |
|---|---|
| 审单超时 / 拒付通知格式 | 14 + 16 |
| 提单 / 装船批注 / 转运 | 19-25 + 26 + 27 |
| 保险 | 28 |
| 金额 / 数量 / 分批 | 30 + 31 + 32 |
| 单据语言 / 交单银行 | 35 |

## Grep 关键词

```bash
# 例：审单时限
Grep "five banking days following" references/rules/UCP_600.md

# 例：拒付通知格式
Grep "single notice" references/rules/UCP_600.md

# 例：保险条款
Grep "insurance" references/rules/UCP_600.md
```