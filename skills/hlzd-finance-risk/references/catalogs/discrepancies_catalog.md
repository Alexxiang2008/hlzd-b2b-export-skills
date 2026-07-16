# 不符点目录（Discrepancies Catalog）

> **用法**：审单步骤 [8] 检测到不符点时，先 `Read` 名称 + ID，再用 `Read references/rules/<file>.md` 引用具体 Article/Rule。
> **覆盖**：UCP 600 15 类 + ISP98 4 类 + URDG 758 3 类 = 共 22 类。

---

## UCP 600 / ISBP 745 不符点（15 类）

### D-UCP-001: 过期提示
- **检测**：`presentation_date > expiry_date`
- **严重度**：CRITICAL
- **来源**：UCP 600 Article 6 + 14
- **建议**：无法交单 → 立即要求展期（如可）或放弃

### D-UCP-002: 超出装运日
- **检测**：`shipment_date > latest_shipment_date`
- **严重度**：CRITICAL
- **来源**：UCP 600 Article 6
- **建议**：无法装运 → 要求改证延长装期

### D-UCP-003: 交单期不符
- **检测**：`presentation_date - shipment_date > 21 days`（默认）
- **严重度**：HIGH
- **来源**：UCP 600 Article 14(c)
- **建议**：要求改证延长交单期

### D-UCP-004: 保险险种不符
- **检测**：保险单险种 ≠ L/C 要求
- **严重度**：HIGH
- **来源**：UCP 600 Article 28
- **建议**：重出保险单 / 要求改证

### D-UCP-005: 保险金额不足
- **检测**：`insurance_amount < goods_amount * 1.1`（默认 CIF 110%）
- **严重度**：HIGH
- **来源**：UCP 600 Article 28(f)
- **建议**：补保险 / 要求改证降低

### D-UCP-006: 提单装船批注缺失
- **检测**：`received for shipment` 但无 `shipped on board` 批注
- **严重度**：HIGH
- **来源**：UCP 600 Article 20(a)(ii) + 27
- **建议**：补批注或重出 B/L

### D-UCP-007: 转运不符（违反 L/C 禁运条款）
- **检测**：L/C 禁止转运但 B/L 显示转运
- **严重度**：HIGH
- **来源**：UCP 600 Article 20(c)
- **建议**：要求 L/C 改允许转运 / 或改运输方式

### D-UCP-008: 装货港 / 卸货港不符
- **检测**：`port_of_loading ≠ LC` 或 `port_of_discharge ≠ LC`
- **严重度**：HIGH
- **来源**：UCP 600 Article 14(f)
- **建议**：要求改证 / 或修改运输

### D-UCP-009: 货物描述不符
- **检测**：`invoice_goods_description ≠ LC_goods_description`
- **严重度**：HIGH
- **来源**：UCP 600 Article 18 + ISBP A26
- **建议**：重开发票 / 要求改证

### D-UCP-010: 金额超限
- **检测**：`invoice_amount > LC_amount * 1.1`
- **严重度**：HIGH
- **来源**：UCP 600 Article 30
- **建议**：降低发票金额 / 要求增额改证

### D-UCP-011: 单据签字缺失
- **检测**：要求签字的单据无签字
- **严重度**：MEDIUM
- **来源**：ISBP 745 A23
- **建议**：补签字（如可）/ 重出单据

### D-UCP-012: 单据日期晚于交单日
- **检测**：`document_date > presentation_date`
- **严重度**：MEDIUM
- **来源**：UCP 600 Article 14(f) + ISBP A7
- **建议**：重出单据（日期不能晚于交单日）

### D-UCP-013: 原单据 vs 副本混淆
- **检测**：L/C 要求 2 正 1 副，但提交 1 正 2 副
- **严重度**：MEDIUM
- **来源**：UCP 600 Article 17 + ISBP A19
- **建议**：补齐 / 重出

### D-UCP-014: 非单据条件
- **检测**：L/C 含 `documents not required` 类条件（如"客户满意证明"未明确签发人）
- **严重度**：HIGH
- **来源**：UCP 600 Article 14(f) + ISBP A41
- **建议**：视为未规定 / 要求改证明确

### D-UCP-015: 审单超 5 银行工作日（拒付通知）
- **检测**：`refusal_notice_date - presentation_date > 5 days`
- **严重度**：HIGH
- **来源**：UCP 600 Article 16
- **建议**：开证行丧失拒付权利 → 受益人可要求付款

---

## ISP98 不符点（4 类）

### D-ISP-001: 备用 L/C 审单超 3 个银行工作日
- **检测**：`review_time > 3 banking days`
- **严重度**：HIGH
- **来源**：ISP98 Rule 4.01
- **建议**：ISP98 审单时限比 UCP 600 严（3 天 vs 5 天）

### D-ISP-002: 备用 L/C 拒付通知超期
- **检测**：`refusal_notice_time > 4 banking days after presentation`
- **严重度**：HIGH
- **来源**：ISP98 Rule 5.03
- **建议**：拒付通知必须在 3 天审单 + 1 天通知 = 4 天内发出

### D-ISP-003: 备用 L/C 缺少不可撤销声明
- **检测**：`'irrevocable' not in standby text`
- **严重度**：LOW（默示不可撤销）
- **来源**：ISP98 Rule 1.06(a)
- **建议**：建议明确写入以避免争议

### D-ISP-004: 电子提示未授权
- **检测**：`electronic presentation without authorization`
- **严重度**：MEDIUM
- **来源**：ISP98 Rule 3.06
- **建议**：备用 L/C 如允许电子提示，应明确授权方式

---

## URDG 758 不符点（3 类）

### D-URDG-001: 保函缺少 supporting statement 要求
- **检测**：无 supporting statement 要求
- **严重度**：HIGH
- **来源**：URDG 758 Article 15
- **建议**：URDG 758 Article 15 强制要求 supporting statement

### D-URDG-002: 保函超过 7 个银行工作日未付款
- **检测**：`payment_time > 7 banking days`
- **严重度**：HIGH
- **来源**：URDG 758 Article 12
- **建议**：URDG 758 要求审单 + 付款 = 7 天内完成

### D-URDG-003: 反担保缺少关键条款
- **检测**：counter-guarantee 缺金额 / 到期日 / 适用规则
- **严重度**：MEDIUM
- **来源**：URDG 758 Article 31-35
- **建议**：反担保应明确金额、到期日、适用规则

---

## 综合风险评级（自动）

```
风险分 = 不符点数 × 5 + 软条款数 × 3 + 银行风险分（0-10）

HIGH    : 风险分 ≥ 15  OR  含 CRITICAL 不符点  OR  制裁国银行
MEDIUM  : 风险分 8-14
LOW     : 风险分 < 8
```

---

## Grep 用法

```bash
# 按 ID 查不符点
Grep "D-UCP-001" references/catalogs/discrepancies_catalog.md

# 按检测关键词搜 L/C
Grep -i "presentation period" <lc_text>

# 按规则库查
Grep "ISP98" references/catalogs/discrepancies_catalog.md
```