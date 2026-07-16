# hlzd-customer-profile — Deep Dive

> 本文件收纳 SKILL.md 因 500 行约束移出的细节章节，仅供 deep-load 参考。


| 异常 | 处理 |
|---|---|
| `PersonaNotFound` | 返回空画像 + 提示新建 |
| `LowConfidenceError` | 提示业务员确认关键字段 |
| `InvalidFieldTypeError` | 类型校验失败，提示正确格式（借鉴 Twenty 字段类型化） |
| `ConflictingDataError` | 多源数据冲突，提示业务员手动确认 |
| `SanctionedCountryError` | CRITICAL，禁止写入画像 |

---

## 自动串联规则

```markdown
## 自动串联

### 上游（被谁触发）
- HLZD-询盘响应: 接到询盘 → 加载客户画像（v0.2 新增: 同时返回跟进建议）
- HLZD-智能报价: 客户询价 → 加载客户画像（v0.2 新增: 推荐报价档位）
- HLZD-物流装箱: 订单确认 → 加载客户偏好（运输方式/包装）
- HLZD-信用证审单: L/C 审单 → 加载客户国别风险
- HLZD-日报助手: 每日 18:00 → 加载客户维度的活跃度统计

### 下游（触发谁）
- AI 跟进建议生成 → 写入飞书卡片 → 业务员确认/编辑/执行
- AI 客群聚合 → 周报/月报自动输出群体洞察

### 被动串联
- 客户新邮件/IM → 自动更新 stats + interests
- 客户新订单 → 自动更新 stats + tier
- 客户节日临近 → 自动提醒业务员
```

---

## 验证清单

- [ ] mb skills list 看到 hlzd-customer-persona
- [ ] 创建客户画像（新建/从现有客户）
- [ ] 字段类型校验（email/phone/uuid/decimal）
- [ ] 评级算法准确度（7 维度加权）
- [ ] AI 跟进建议生成（5 类建议）
- [ ] AI 客群聚合（按国家/行业/等级）
- [ ] 跨 skill 查询（智能报价/询盘响应/信用证审单都能读）
- [ ] SQLite 数据库性能（10,000 客户画像）
- [ ] 置信度动态更新
- [ ] 字段分类清晰（核心/基础/行为/自定义）

---

## 性能目标

| 路径 | p99 目标 | 预估 |
|---|---|---|
| 创建/更新画像 | < 1s | 0.3s |
| 评级算法 | < 0.5s | 0.1s |
| 跟进建议生成 | < 2s | 0.8s |
| 客群聚合（100 客户）| < 5s | 2-3s |
| 客群聚合（10,000 客户）| < 30s | 15-25s |
| 跨 skill 查询 | < 0.5s | 0.1s |

---

## 安全考虑

1. 客户数据隔离——客户画像仅授权业务员可见
2. 跨租户隔离——不同 HLZD 子公司数据不混淆（v0.2 设计预留）
3. 审计日志——画像变更记录保存 5 年
4. PII 加密——客户敏感信息（电话/邮箱）入库前加密（v0.3 升级，借鉴 Tracardi）
5. GDPR 合规——欧盟客户可申请删除（v0.3 升级）

---

## 已知限制（v0.2 接受）

1. **不接实时 CRM 同步**——画像独立维护，不与外部 CRM 同步
2. **不接社交媒体数据**——客户画像只基于 HLZD 内部交互
3. **不接实时行为追踪**——不像 Tracardi 那样做实时 CDP（不是 HLZD 业务核心）
4. **多租户隔离未实现**——v0.2 设计预留 workspace_id 字段，v0.3 实现
5. **PII 哈希未实现**——v0.3 借鉴 Tracardi 实现（GDPR 合规）
6. **跟进建议基于规则**——不是 LLM 生成（v0.3 升级）

---

## 后续路线

| 版本 | 新增 |
|---|---|
| v0.2 | ✅ Tracardi 字段分类 + Twenty 字段类型化 + 1688 跟进建议 + 1688 客群聚合 |
| **v0.3** | 多租户隔离（workspace_id 字段 + Panmira Drizzle ORM）|
| **v0.3** | PII 哈希（借鉴 Tracardi，GDPR 合规）|
| **v0.3** | LLM 生成跟进建议（升级规则版到 LLM 版）|
| v0.4 | 实时 CRM 同步（与外部 CRM 数据互通）|
| v0.4 | 社交媒体数据接入（领英/微信/WhatsApp）|

---

## 文件位置

```
目标位置: ~/.claude/skills/hlzd-customer-persona/
SKILL.md: ~/.claude/skills/hlzd-customer-persona/SKILL.md
config/schema.yaml: ~/.claude/skills/hlzd-customer-persona/config/schema.yaml
references/: ~/.claude/skills/hlzd-customer-persona/references/
scripts/: ~/.claude/skills/hlzd-customer-persona/scripts/
```

注册命令（HLZD skill 自动发现）：
```bash
mb skills install hlzd-customer-persona 青囊
```

---

## v0.2 vs v0.1 升级对比

| 维度 | v0.1 | v0.2 |
|---|---|---|
| 字段模型 | flat 5 层 25 项 | **4 层分类**（借鉴 Tracardi）|
| 字段类型 | free-form | **类型化**（借鉴 Twenty）|
| 跟进建议 | 无 | **AI 生成**（借鉴 1688）⭐ |
| 客群聚合 | 无 | **AI 聚合**（借鉴 1688）⭐ |
| 借鉴项目 | 0 | **6 个开源项目** |
| 工作量 | 2.5 天 | **5 天（+2.5 天）** |
| 跨 skill 共享 | SQLite + 统一 schema | **保留 + 增强** |

---

**END of HLZD-客户画像 v0.2 SKILL.md**

**6 个借鉴项目**：
- 🏆 Tracardi/tracardi (646 stars) — 4 层字段分类 + PII 哈希
- 🏆 twentyhq/twenty (52,256 stars) — 字段类型化 + 多租户
- 🏆 next-1688/1688-customer-opportunity (837 stars) — AI 客群 + 跟进建议
- PostHog/posthog (35,350 stars) — 单一栈整合
- Frappe/crm (2,924 stars) — 完整业务实体
- Monica (24,837 stars) — 简单关系模型