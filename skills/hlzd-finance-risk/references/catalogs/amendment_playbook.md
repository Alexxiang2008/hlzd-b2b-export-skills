# 改单建议与谈判话术（Amendment Playbook）

> **用法**：审单步骤 [12] 生成改单清单 + 谈判话术，按不符点类型选择模板。

---

## 改单清单模板（按严重度排序）

### CRITICAL 不符点（必须立即处理）

| ID | 改单建议模板 |
|---|---|
| D-UCP-001 | "L/C 已过期，请开证行出具 L/C 展期确认（amendment extending expiry to [NEW DATE]）。我方在收到展期确认前不安排装运。" |
| D-UCP-002 | "装运期已过，请开证行出具装期延长确认（amendment extending latest shipment date to [NEW DATE]）。" |

### HIGH 不符点（建议要求改证）

| ID | 改单建议模板 |
|---|---|
| D-UCP-003 | "交单期 [X] 天过短，请开证行将交单期延长至 21 天（UCP 600 Article 14(c) 默认值）。" |
| D-UCP-005 | "保险金额不足 CIF 110%，请开证行修改保险条款或降低货值要求。" |
| D-UCP-007 | "L/C 禁止转运但实际运输需转运，请开证行删除禁止转运条款或允许转运。" |
| D-URDG-001 | "URDG 758 Article 15 要求 supporting statement，请开证行/担保人明确索款必须附 supporting statement。" |

### MEDIUM 不符点（可接受也可改）

| ID | 改单建议模板 |
|---|---|
| D-UCP-011 | "[单据名] 缺签字，请签发人补签字。" |
| D-UCP-014 | "L/C 含非单据条件 '[XXX]'，建议删除或改为单据化表述（如指定签发人）。" |

---

## 谈判话术（按场景）

### 场景 1：客户坚持保留软条款
**话术**：
> "此条款触发 [UCP 600 Article X / ISP98 Rule X / URDG 758 Article X] 风险，**审单时银行可据此拒付**。建议改为 [具体替代方案]，否则我方将要求：
> 1. 客户书面承担银行拒付风险
> 2. L/C 金额上调 10% 作为风险准备金
> 3. 改用 [DP / DA / TT] 等风险更低的付款方式"

### 场景 2：开证行/担保人对改单消极
**话术**：
> "请开证行在 [X] 个银行工作日内确认改单，否则我方将：
> 1. 暂停备货
> 2. 援引 [UCP 600 Article X / ISP98 Rule X / URDG 758 Article X] 主张 L/C 无效
> 3. 启动合同违约条款"

### 场景 3：对方拒绝 supporting statement
**话术**：
> "URDG 758 Article 15 强制要求 supporting statement。如贵方拒绝，将适用 UCP 600 兜底（Article 1 兜底条款），但将丧失 URDG 758 的明确性优势。我方仍可接受，但建议贵方重新评估。"

---

## 改单优先级矩阵

| 严重度 | 不符点数量 | 行动 |
|---|---|---|
| CRITICAL | 任意 | 立即停止备货 + 紧急改证 |
| HIGH | ≥ 2 | 强烈要求改证 / 拒绝接受 |
| MEDIUM | ≥ 3 | 要求改证 / 接受需客户书面免责 |
| LOW | 任意 | 可接受 |

---

## 跨 skill 触发

- **改单后** → 自动调 HLZD-智能报价 重算报价（运保费 / 包装可能变）
- **拒付风险高** → 自动调 HLZD-客户画像 更新客户风险等级
- **接受改单** → 自动调 HLZD-email-group 起草接受通知

---

## Grep 用法

```bash
# 按场景查话术
Grep "场景 1" references/catalogs/amendment_playbook.md

# 按 ID 查改单模板
Grep "D-UCP-003" references/catalogs/amendment_playbook.md
```