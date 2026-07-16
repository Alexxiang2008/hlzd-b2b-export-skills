# HLZD 信用证审单 — 端到端测试场景

> **用法**：每个场景对应一个真实业务样本，验证 14 步工作流 + 三套规则库适配。
> **测试模式**：手工触发（Claude 读样本 → 走流程 → 对照预期）。
> **自动化**：scripts/orchestrator.py 可单独跑检测（无需 OCR）。

---

## 场景 1：Commercial LC（UCP 600 + ISBP 745）

**样本类型**：商业跟单信用证  
**HLZD 角色**：受益人（Beneficiary）  
**预期 L/C 类型**：`COMMERCIAL_LC`  
**预期规则库**：UCP 600 + ISBP 745

### 测试步骤

```bash
python scripts/orchestrator.py --text "DOCUMENTARY CREDIT UCP 600. APPLICANT: ACME CORP. BENEFICIARY: HLZD INDUSTRIAL CO LTD. ..." --role beneficiary
```

### 预期输出（关键字段）

```json
{
  "doc_type": "ISSUED",
  "lc_type": "COMMERCIAL_LC",
  "role": "BENEFICIARY",
  "soft_clauses": [...],
  "risk_level": "LOW"  // 或 MEDIUM/HIGH 取决于软条款数
}
```

### 验证清单

- [ ] L/C 类型识别为 `COMMERCIAL_LC`
- [ ] 角色识别为 `BENEFICIARY`
- [ ] 软条款扫描命中（如有 applicant approval 类条款）
- [ ] 引用 UCP 600 + ISBP 745 条文（按 references/index/）

---

## 场景 2：Standby LC（ISP98）

**样本类型**：备用信用证（Performance Standby）  
**HLZD 角色**：受益人  
**预期 L/C 类型**：`PERFORMANCE_STANDBY`  
**预期规则库**：ISP98

### 测试步骤

```bash
python scripts/orchestrator.py --text "IRREVOCABLE STANDBY LETTER OF CREDIT. PERFORMANCE STANDBY. ISP98. APPLICANT: ACME. BENEFICIARY: HLZD." --role beneficiary
```

### 预期输出

```json
{
  "doc_type": "ISSUED",
  "lc_type": "PERFORMANCE_STANDBY",
  "role": "BENEFICIARY",
  "soft_clauses": [
    {"id": "SC-ISP-003", "risk": "LOW"}  // 如缺 irrevocable 明示
  ]
}
```

### 验证清单

- [ ] L/C 类型识别为 `PERFORMANCE_STANDBY`
- [ ] 引用 ISP98 Rule 1.06 / 4.01 / 5.01-5.03（如有拒付风险评估）
- [ ] 软条款扫描过滤 UCP 600 条款

---

## 场景 3：Demand Guarantee（URDG 758）

**样本类型**：见索即付保函（投标担保）  
**HLZD 角色**：担保人（Guarantor）  
**预期 L/C 类型**：`DEMAND_GUARANTEE`  
**预期规则库**：URDG 758

### 测试步骤

```bash
python scripts/orchestrator.py --text "DEMAND GUARANTEE URDG 758. APPLICANT: ACME. BENEFICIARY: HLZD. GUARANTOR: HLZD BANK." --role guarantor
```

### 预期输出

```json
{
  "doc_type": "ISSUED",
  "lc_type": "DEMAND_GUARANTEE",
  "role": "GUARANTOR",
  "soft_clauses": [
    {"id": "SC-URDG-001", "risk": "HIGH"}  // 如缺 supporting statement
  ]
}
```

### 验证清单

- [ ] L/C 类型识别为 `DEMAND_GUARANTEE`
- [ ] 角色识别为 `GUARANTOR`
- [ ] 引用 URDG 758 Article 15（supporting statement）
- [ ] 软条款扫描过滤 UCP/ISP 条款

---

## 场景 4：模板检测

**样本类型**：含 [Insert XXX] 占位符的模板  
**预期文档类型**：`TEMPLATE`

### 测试步骤

```bash
python scripts/orchestrator.py --text "DOCUMENTARY CREDIT. APPLICANT: [Insert Applicant Name]. BENEFICIARY: [Insert Beneficiary Name]. AMOUNT: [Insert Amount]. EXPIRY: [Insert Expiry Date]."
```

### 预期输出

```json
{
  "doc_type": "TEMPLATE",
  "template_placeholders": ["[insert applicant name]", ...],
  "status": "TEMPLATE_DETECTED"
}
```

### 验证清单

- [ ] 文档类型识别为 `TEMPLATE`
- [ ] 占位符列表返回
- [ ] 流程在步骤 [2] 终止（不进入 L/C 类型识别）

---

## 场景 5：草稿检测

**样本类型**：含 "DRAFT" 关键词的草稿  
**预期文档类型**：`DRAFT`

### 测试步骤

```bash
python scripts/orchestrator.py --text "DRAFT DOCUMENTARY CREDIT UCP 600 (FOR REFERENCE ONLY). ..."
```

### 预期输出

```json
{
  "doc_type": "DRAFT",
  "status": "DRAFT_DETECTED"
}
```

### 验证清单

- [ ] 文档类型识别为 `DRAFT`
- [ ] 提示等待正式版

---

## 场景 6：未知类型

**样本类型**：无明显关键词的文本  
**预期 L/C 类型**：`UNKNOWN`

### 测试步骤

```bash
python scripts/orchestrator.py --text "Random text about international trade."
```

### 预期输出

```json
{
  "doc_type": "ISSUED",
  "lc_type": "UNKNOWN",
  "status": "OK"
}
```

### 验证清单

- [ ] L/C 类型识别为 `UNKNOWN`
- [ ] 默认按 Commercial 处理 + 提示人工确认

---

## 性能基线（p99）

| 路径 | 目标 | 实测 |
|---|---|---|
| L/C 类型识别 | < 0.5s | ___ |
| 文档类型识别 | < 0.5s | ___ |
| 角色识别 | < 0.5s | ___ |
| 软条款扫描（含 catalog I/O） | < 1s | ___ |
| 不符点检测（基于字段） | < 2s | ___ |
| 全流程 | < 30s | ___ |

---

## 渐进式披露验证

**关键验证**：SKILL.md 加载量 vs 全文加载量

| 维度 | 全文加载（v0.2） | 渐进式披露（v0.3） |
|---|---|---|
| 触发时上下文 | 32KB | **~7KB**（SKILL.md） |
| 审单时增量加载 | 0（已全部加载） | **5-15KB**（按需 Read 单 Article） |
| 总加载峰值 | 32KB + OCR + L/C | **~22KB**（SKILL.md + 必要条文 + L/C） |

**验证方法**：
1. 跑 `wc -c HLZD-信用证审单/SKILL.md` → 应 < 8KB
2. 跑 `wc -c references/rules/*.md` → 验证规则全文确实在 references/ 下
3. Claude Code 中触发 skill → 检查实际加载的 tokens

---

## 回归测试清单

- [ ] orchestrator.py --help 不触发子模块加载（Windows GBK 安全）
- [ ] detect_lc_type.py 4 类全覆盖（COMMERCIAL / STANDBY / GUARANTEE / UNKNOWN）
- [ ] detect_doc_type.py 3 类全覆盖（TEMPLATE / DRAFT / ISSUED）
- [ ] detect_role.py 3 类全覆盖（APPLICANT / BENEFICIARY / GUARANTOR）
- [ ] scan_soft_clauses.py 按规则库过滤（不跨库命中）
- [ ] detect_discrepancies.py 按规则库分支（UCP/ISP/URDG 三套）