---
name: hlzd-customer-profile
description: "B2B 客户 360° 画像 —— 4 层字段模型（基础/交易/行为/画像）+ AI 跟进建议 + AI 客群聚合 + 5 维评级（A/B/C/D）。与 hlzd-customer-due-diligence 互补：due-diligence = 合规粗筛，customer-profile = 深度画像。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: customer-profile
  triggered_by:
    - 客户画像
    - 客户档案
    - 客户 360
    - 客户标签
    - 客户评级
    - 客户分层
    - 客户运营
    - 客户聚合
    - 客群分析
    - 跟进建议
    - customer profile
    - customer 360
    - customer scoring
    - account-based marketing
    - lead nurturing
---

# HLZD 客户画像 v0.2

> **v0.2 升级说明**（基于 GitHub 调研 6 个开源项目）：
> 1. **借鉴 Tracardi CDP**（646 stars）的 4 层字段分类（核心/基础/行为/自定义）
> 2. **借鉴 Twenty CRM**（52,256 stars）的字段类型化（enum/decimal/datetime/composite）
> 3. **借鉴 1688 客户运营**（837 stars）的 AI 客群聚合 + 跟进建议生成
> 4. **保留 v0.1 的 5 层 25 项**业务维度（基础/需求/痛点/偏好/分层）

---

## 定位

| 对比项 | 通用工具（CRM/Excel） | **HLZD-客户画像 v0.2** |
|---|---|---|
| 字段模型 | flat 字段表 | **4 层分类**（核心/基础/行为/自定义，借鉴 Tracardi）|
| 字段类型 | 字符串混杂 | **类型化**（enum/decimal/datetime/composite，借鉴 Twenty）|
| 客户分群 | 人工分类 | **AI 自动客群聚合**（借鉴 1688）|
| 跟进建议 | 经验主义 | **AI 跟进建议生成**（借鉴 1688）|
| 多维度评分 | 单一分数 | **7 维度加权评分**（v0.1）|
| 跨 skill 共享 | 各 skill 自定义 | **统一 schema + SQLite**（v0.1）|

**核心原则**：客户画像不是"数据库表"，是"业务员和 AI 协同决策的事实源"。

---

## 数据源借鉴（GitHub 调研）

| 借鉴项目 | Stars | 借鉴内容 |
|---|---|---|
| **Tracardi/tracardi** | 646 | 4 层字段分类（核心/基础/行为/自定义）+ PII 哈希 |
| **Twenty/twentyhq** | 52,256 | 字段类型化（Address/Email/Phone/FullName/Currency） |
| **1688-customer-opportunity** | 837 | AI 客群分类 + 跟进建议 + 客户机会监控 |
| **PostHog/posthog** | 35,350 | 单一栈整合 + Feature Flag |
| **Frappe/crm** | 2,924 | 完整业务实体设计 |
| **Monica** | 24,837 | 简单关系模型 |

---

## v0.2 核心架构 — 4 层字段模型（借鉴 Tracardi）

### 字段分类总览

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 0: 核心标识 (Core Identity)                            │
│ - customer_id (主键)                                         │
│ - ids (多 ID 合并列表)                                       │
│ - metadata (created_at / updated_at / confidence)            │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: 基础档案 (Basic Profile)                            │
│ - 公司信息 / 联系人 / 工商信息                                │
│ - 借鉴 Tracardi 的 `data` 字段                               │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: 行为画像 (Behavioral)                                │
│ - stats: 订单/询盘/响应次数                                  │
│ - interests: 兴趣度评分                                      │
│ - preferences: 偏好                                          │
│ - pain_points: 痛点                                          │
│ - 借鉴 Tracardi 的 `stats/interests/consents`                │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: 业务自定义 (Custom)                                   │
│ - tier: 分层评级                                              │
│ - traits: HLZD 自定义属性                                     │
│ - tags: 多维度标签                                            │
│ - aux: 辅助数据（授权状态）                                  │
│ - 借鉴 Tracardi 的 `traits/aux/trash`                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 完整 schema v0.2（借鉴 Tracardi + Twenty）

```yaml
# ~/.claude/skills/hlzd-customer-persona/config/schema.yaml
# 客户画像标准 schema —— 所有 skill 都按这个读

customer_persona_schema_v2:

  # ===== Layer 0: 核心标识 (借鉴 Tracardi ids/metadata) =====
  customer_id:
    type: uuid
    primary_key: true
    description: "客户唯一标识"

  ids:
    type: list[string]
    description: "多 ID 合并列表（邮箱哈希/电话哈希/工商注册号/海关编码）"

  created_at:
    type: datetime

  updated_at:
    type: datetime

  updated_by:
    type: enum[string]
    options: ["业务员手动", "AI 自动推断", "客户主动更新"]
    default: "AI 自动推断"

  confidence:
    type: float
    range: [0.0, 1.0]
    description: "画像可信度（初始低，每次互动 +0.05，最高 0.95，业务员确认 = 1.0）"

  # ===== Layer 1: 基础档案 (借鉴 Tracardi data) =====
  basic:
    company_name_cn:
      type: string
      description: "公司中文名"
    company_name_en:
      type: string
      description: "公司英文名"
    country:
      type: enum[string]
      source: "ISO 3166"
      description: "国家代码（影响银行风险评级）"
    industry:
      type: enum[string]
      options: ["机械", "设备", "建材", "化工", "电子", "汽车", "纺织", "其他"]
    annual_revenue_usd:
      type: decimal
      description: "年营收（美元）"
    contact_persons:
      type: list[contact]
      structure:
        name: string
        title: enum[string]  # 决策人/影响人/使用人/财务
        email: email
        phone: phone
        whatsapp: phone
        preferred_contact_method: enum[string]

  # ===== Layer 2: 行为画像 (借鉴 Tracardi stats/interests) =====

  # 2.1 stats（借鉴 Tracardi stats）
  stats:
    order_count: int
    inquiry_count: int
    email_count: int
    im_count: int
    phone_count: int
    avg_response_time_hours: decimal
    payment_on_time_rate: float  # 0-1
    last_contact_date: datetime
    last_order_date: datetime

  # 2.2 interests（借鉴 Tracardi interests，命名兴趣度评分）
  interests:
    type: dict[string, float]  # 产品类别 → 兴趣度 0-1
    example:
      "石油套管": 0.85
      "阀门": 0.30
      "建材": 0.10

  # 2.3 preferences（v0.1 保留）
  preferences:
    communication:
      channel: enum[string]  # 邮件/微信/WhatsApp/电话
      time: enum[string]       # 北京时间/客户当地时间
      language: enum[string]   # 中/英/俄/阿/西
      response_speed_hours: int
    decision:
      chain_length: enum[int]  # 1 人 / 3-5 人 / 委员会
      speed: enum[string]      # 快/慢/极慢
    quote_format:
      format: enum[string]     # PDF/Excel/微信截图/视频会议
      detail_level: enum[string] # 只报最低/多档对比/详细拆解
      validity_days: int
    cultural:
      holidays: list[string]
      communication_style: enum[string]  # 直接/委婉/数据驱动/关系导向
      taboos: list[string]

  # 2.4 pain_points（v0.1 保留）
  pain_points:
    business_pain: list[string]
    relationship_pain: list[string]
    decision_maker_kpi: string

  # ===== Layer 3: 业务自定义 (借鉴 Tracardi traits/aux/tags) =====

  # 3.1 tier（v0.1 保留）
  tier:
    grade:
      type: enum[string]
      options: ["VIP", "A", "B", "C", "BLACKLIST"]
    score:
      type: int
      range: [0, 100]
      description: "7 维度加权评分"
    tags: list[string]  # 多维度标签

  # 3.2 traits（借鉴 Tracardi traits - 开放键值对）
  traits:
    type: dict[string, any]
    description: "HLZD 自由扩展字段（如行业 KPI/特殊要求）"

  # 3.3 aux（借鉴 Tracardi aux - 辅助数据）
  aux:
    type: dict[string, any]
    description: "授权状态/系统元数据"

  # ===== 借鉴 Twenty 的字段类型化 =====
  field_types:
    email: r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    phone: r"^\+?[0-9\s\-\(\)]{7,20}$"
    uuid: r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    decimal: r"^-?\d+(\.\d+)?$"
    datetime: r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
```

---

## v0.2 新增 — AI 跟进建议生成（借鉴 1688 客户运营）

### scripts/generate_followup_advice.py

```python
"""
借鉴 1688-customer-opportunity 项目的"买家成交机会"功能
输入: 客户画像
输出: 3-5 条跟进建议
"""

from customer_persona import Persona

def generate_followup_advice(customer_id: str) -> list[dict]:
    persona = load_persona(customer_id)
    advice_list = []

    # 1. 联系时机建议
    last_contact = persona.stats.last_contact_date
    days_since = (now() - last_contact).days
    if days_since > 7:
        advice_list.append({
            "type": "TIMING",
            "priority": "HIGH",
            "advice": f"客户上次联系是 {days_since} 天前，建议 24h 内主动联系",
        })

    # 2. 报价档位建议（基于客户等级）
    quote_tier_map = {
        "VIP": "最高档 + 特别折扣",
        "A": "标准档 + 阶梯折扣",
        "B": "标准档",
        "C": "基础档",
    }
    advice_list.append({
        "type": "QUOTE_TIER",
        "priority": "HIGH",
        "advice": f"客户等级 {persona.tier.grade}，建议报价档位: {quote_tier_map[persona.tier.grade]}",
    })

    # 3. 沟通风格建议（基于偏好）
    advice_list.append({
        "type": "COMMUNICATION",
        "priority": "MEDIUM",
        "advice": f"客户偏好 {persona.preferences.communication.channel} + "
                  f"{persona.preferences.communication.language}，"
                  f"按此风格起草沟通内容",
    })

    # 4. 报价单格式建议
    advice_list.append({
        "type": "QUOTE_FORMAT",
        "priority": "MEDIUM",
        "advice": f"客户偏好 {persona.preferences.quote_format.format} + "
                  f"{persona.preferences.quote_format.detail_level} 详细度",
    })

    # 5. 文化敏感建议
    if persona.preferences.cultural.holidays:
        advice_list.append({
            "type": "CULTURAL",
            "priority": "LOW",
            "advice": f"避免在客户节日 {persona.preferences.cultural.holidays} 提涨价",
        })

    return advice_list
```

---

## v0.2 新增 — AI 客群聚合（借鉴 1688 客群列表）

### scripts/aggregate_segments.py

```python
"""
借鉴 1688-customer-opportunity 项目的"AI 客群列表"功能
输入: 所有客户画像
输出: 按维度聚合的客户群体洞察
"""

from collections import defaultdict
from customer_persona import list_all_personas

def aggregate_segments() -> dict:
    """按国家/行业/客户等级聚合客户"""
    personas = list_all_personas()
    segments = defaultdict(lambda: {
        "count": 0,
        "common_traits": [],
        "common_pain_points": [],
        "common_preferences": [],
        "avg_order_amount_usd": 0,
        "conversion_rate": 0,
        "total_orders": 0,
    })

    for p in personas:
        # 按国家聚合
        country = p.basic.country
        segments[country]["count"] += 1
        # ... 累计各项指标

    # 计算群体洞察
    for seg_key, seg in segments.items():
        seg["common_traits"] = find_common(seg["members"], field="traits")
        seg["common_pain_points"] = find_common(seg["members"], field="pain_points")
        seg["common_preferences"] = find_common(seg["members"], field="preferences")

    return dict(segments)
```

### 客群聚合示例输出

```yaml
# 飞书卡片展示
中东客户群体:
  客户数: 23
  共性特征:
    - 普遍要 DAP 报价
    - 偏好 30% TT + 70% LC at sight
    - 节日: 开斋节（Ramadan 后 1 周）
    - 忌讳: 政治话题
  平均订单金额: 45000 USD
  成交率: 68%
  建议话术: "强调 INCOTERMS DAP 和发货前 SGS 检验"

俄罗斯客户群体:
  客户数: 8
  共性特征:
    - 因制裁偏好中欧班列运输
    - 偏好 EXW 报价（避免俄罗斯清关风险）
    - 关注银行制裁风险
  平均订单金额: 32000 USD
  成交率: 45% (制裁导致拒付率高)
  建议话术: "提示客户走欧洲银行保兑"
```

---

## 评级算法 v0.2（保留 v0.1）

```python
def calculate_score_v2(persona) -> int:
    """v0.2 评级算法（保留 v0.1 7 维度加权）"""
    score = 0

    # 购买力（30 分）
    annual_order = persona.basic.annual_revenue_usd
    if annual_order > 1_000_000: score += 30
    elif annual_order > 300_000: score += 22
    elif annual_order > 100_000: score += 15
    elif annual_order > 30_000: score += 8
    else: score += 3

    # 合作年限（10 分）
    years = (now() - persona.basic.first_contact_date).days / 365
    score += min(int(years * 2), 10)

    # 付款准时率（15 分）
    score += int(persona.stats.payment_on_time_rate * 15)

    # 沟通响应（10 分）
    response_hours = persona.stats.avg_response_time_hours
    if response_hours < 24: score += 10
    elif response_hours < 72: score += 6
    else: score += 3

    # 增长趋势（15 分）
    growth = persona.aux.get("growth_trend", 0)
    if growth >= 0.5: score += 15
    elif growth >= 0: score += 8
    else: score += 2

    # 信用记录（10 分）
    if persona.tier.tags and "信用良好" in persona.tier.tags:
        score += 10
    elif persona.tier.tags and "信用一般" in persona.tier.tags:
        score += 5

    # 推荐价值（10 分）
    referral_count = persona.aux.get("referral_count", 0)
    score += min(referral_count * 2, 10)

    return min(score, 100)
```

---

## scripts/ 设计 v0.2

```
scripts/
├── schema.py                     # schema 定义（借鉴 Tracardi 4 层）
├── database.py                   # SQLite + 统一 schema
├── crud_persona.py               # 增删改查
├── grade_customer.py             # 7 维度加权评分（保留 v0.1）
├── generate_followup_advice.py   # ⭐ v0.2 新增: AI 跟进建议（借鉴 1688）
├── aggregate_segments.py         # ⭐ v0.2 新增: AI 客群聚合（借鉴 1688）
├── cross_validate_quote.py       # 关联 HLZD-智能报价
├── cross_validate_inquiry.py     # 关联 HLZD-询盘响应
├── cross_validate_shipment.py   # 关联 HLZD-物流装箱
├── cross_validate_lc.py          # 关联 HLZD-信用证审单
├── search_history.py             # 客户历史搜索
└── orchestrator.py              # 主调度
```

---

## references/ 设计 v0.2

```
references/
├── schema_specification.md      # 完整 schema 规范（借鉴 Tracardi）
├── field_types.md               # 字段类型定义（借鉴 Twenty）
├── followup_advice_playbook.md  # 跟进建议规则库（借鉴 1688）
├── segment_patterns.md          # 客群聚合模式（借鉴 1688）
├── tier_definitions.md          # 分层评级标准
├── cultural_calendar.md         # 文化日历（俄罗斯/中东/拉美节日）
├── banned_countries.md          # 制裁名单
└── examples/
    ├── case_vip_customer.md     # VIP 客户画像完整样例
    ├── case_segment_middle_east.md  # 中东客户群体洞察样例
    ├── case_followup_advice.md  # 跟进建议样例
    └── case_cross_skill_query.md  # 跨 skill 查询样例
```

---

## 错误地图

---

## 更多细节

完整设计文档（v0.1.x 实现细节 + 错误地图 + 性能目标）见 [references/deep-dive.md](references/deep-dive.md)。
