# 5-Dimension Scoring Rubric（HLZD 询盘评估评分细则）

> 版本：v0.1 · 2026-07-15

本文件定义 `hlzd-inquiry-qualify` Skill 的 5 维评分细则。所有维度按下列规则：每一项满分见 SKILL.md。本文件给出**扣分规则**与**A/B/C/D 阈值**。

---

## 总分公式

```
total = D1 + D2 + D3 + D4 + D5
其中 D1..D3 各 25 分，D4 = 15 分，D5 = 10 分，满分 100
```

---

## D1 — 产品需求（满分 25）

| 子项 | 满分 | 满足条件 |
|---|---|---|
| 产品名称 | 8 | 出现具体品类关键词（如"API 5CT Casing"、"Steel Structure"、"Solar Panel"），不是 "your product"|
| 规格型号 | 10 | 出现 1+ 关键技术规格（等级、尺寸、标准号）|
| 数量 | 7 | 出现具体数字 + 单位（米/吨/件/柜）|

**扣分**：每缺失 1 项扣相应满分；名称模糊（"your equipment"）该项 ≤ 2 分。

**典型高分 case**：明确"API 5CT L80 9-5/8" BTC，5000 meters" → D1 = 24
**典型低分 case**："we need some steel products from China, please send catalog" → D1 = 0

---

## D2 — 商务需求（满分 25）

| 子项 | 满分 | 满足条件 |
|---|---|---|
| 目的港 | 6 | 出现完整港口 + 国家（"Jeddah, Saudi Arabia"）|
| 贸易术语 | 6 | 出现 INCOTERMS 2020 标准词（EXW/FOB/CFR/CIF/CIP/DAP/DPU/DDP）|
| 目标价 / 预算 | 8 | 数字 + 币种（"USD 1200 per ton"或"budget USD 50K"）|
| 期望交期 | 5 | 出现明确时间（"2026-Q3"、"by September"）|

**扣分**：币种模糊（"around 1000"未带币种）按 4 分算。

**典型高分**："CIF Jeddah, USD 1300/ton, by Q3 2026" → D2 = 23
**典型低分**：仅端口、无价格、无交期 → D2 = 6

---

## D3 — 技术需求（满分 25）

| 子项 | 满分 | 满足条件 |
|---|---|---|
| 应用场景 | 7 | 出现行业关键词（"oilfield" / "construction" / "hospital" / "solar farm"）|
| 认证要求 | 10 | 出现认证号（API/ISO/UL/CE/RoHS/REACH）|
| 工况参数 | 8 | 至少 2 项（压力 / 温度 / 介质 / 流量 / 电压）|

**缺失如何补**：在 `questions_to_confirm` 列出"please confirm max pressure / temp / media"。

**典型高分**："API 5CT L80 for sour service, NACE MR0175 required, working pressure 5000 psi, H2S partial pressure 0.5 psi" → D3 = 25
**典型低分**："need pipe" → D3 = 0

---

## D4 — 客户信息（满分 15）

| 子项 | 满分 | 满足条件 |
|---|---|---|
| 公司名 | 4 | 完整法定名称（"Saudi Aramco Trading Co." 而非 "Saudi company"）|
| 联系人 + 职位 | 4 | 全名 + 职位（"Mr. Ahmed, Procurement Manager"）|
| 邮箱 | 3 | 业务邮箱（非 gmail/yahoo 的 free mail 加 0；公司邮箱满分）|
| 电话 / WhatsApp | 2 | E.164 或含国家码 |
| LinkedIn / 官网 | 2 | URL |

**扣分**：free email（gmail / yahoo / hotmail / outlook / qq / 163）该项最高 1 分。

**典型高分**：Aramco 采购员，公司邮箱 + LinkedIn → D4 = 15
**典型低分**：仅 "a Chinese supplier: please send best price" → D4 = 0

---

## D5 — 项目背景（满分 10）

| 子项 | 满分 | 满足条件 |
|---|---|---|
| 项目名 / 项目阶段 | 4 | 出现项目名或阶段（"South Ghawar" / "EPC tendering"）|
| EPC / 总包身份 | 2 | 出现"on behalf of X" / "EPC contractor" |
| 招标号 / World Bank Ref | 2 | 出现招标号 / WB 项目号 |
| 时间线 / 里程碑 | 2 | 出现关键节点（"first shipment by 2026-12"）|

**典型高分**：EPC tender 带招标号 + 明确时间线 → D5 = 10
**典型低分**：无任何项目背景 → D5 = 0

---

## 评级阈值

| Grade | 总分 | 响应 SOP |
|---|---|---|
| **A** | 90-100 | 立即分配销售负责人 + 24h 内首次主动回复 + 推荐 senior sales |
| **B** | 70-89 | 分配销售 + 48h 内回复 + 补全 D3/D2 缺失字段后复评 |
| **C** | 50-69 | 入培育池 + 邮件 drip + 90 天后复评 |
| **D** | 0-49 | 自动模板回复 + 归档 + 转入 nurture 序列 |

---

## 边界 case

| 场景 | 处置 |
|---|---|
| 询盘文本 < 50 字 | 强制 Grade = C/D，提示"信息不足" |
| 同一询盘出现多 SKU（D1 + D2 多重）| 各取最具代表性一个，其余列入 notes |
| 询盘包含联系方式但是 spam | 自动标 red_flags 但不让它升 Grade（生效最低 D 提示） |
| 询问目标价"around 1000"无币种 | D2 相应子项按 4 分算 |

---

## 升级记录

| 版本 | 说明 |
|---|---|
| 0.1.0 | 5 维满分别为 25/25/25/15/10，A/B/C/D 阈值 = 90/70/50/0 |

---

*HLZD Cross-Border AI Platform · 2026*
