---
name: hlzd-daily-report
description: "B2B 业务员日报自动化 —— LangBot 事件采集 + LLM 摘要 + 飞书卡片推送 + 次日 8:00 早会总结。ActivityWatch + Inbox Zero + LangBot 三方借鉴。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: operations
  triggered_by:
    - 日报助手
    - 业务员日报
    - 每日总结
    - 周报助手
    - 飞书日报卡片
    - 早会总结
    - 今日工作
    - 明日计划
    - 活动追踪
    - 时间块统计
    - daily report
    - sales daily standup
    - morning briefing
    - activity tracking
    - time blocking
---

# HLZD 日报助手 v0.1

> **关键借鉴**（基于 GitHub 调研 3 个高星标项目）：
> 1. **LangBot**（16,712 stars）—— HLZD 日报助手作为 LangBot 插件运行（不自己写飞书机器人）
> 2. **ActivityWatch**（18,136 stars）—— Event/Bucket 数据模型 + heartbeat 合并
> 3. **Inbox Zero**（11,550 stars）—— Pydantic 结构化输出

**核心原则**：日报不是"写"，是"自动汇总 + 一键确认"——从 4 大数据源（邮件/IM/订单/客户）抽取当日活动 → 结构化日报 → 飞书卡片推送。

---

## 定位

| 对比项 | 手工写日报 | **HLZD-日报助手 v0.1** |
|---|---|---|
| 写日报时间 | 30-60 分钟 | **< 1 分钟**（一键确认）|
| 数据来源 | 人工回忆 | **4 大数据源自动聚合**（邮件/IM/订单/客户）|
| 早会总结 | 临时拼凑 | **昨日日报自动生成 to do list** |
| 待办事项 | 凭感觉 | **基于客户互动 + SLA 自动推荐** |
| 主管 dashboard | 手工汇总 | **每日自动聚合** |

---

## 数据源借鉴

| 借鉴项目 | Stars | 借鉴内容 |
|---|---|---|
| 🏆 **langbot-app/LangBot** | 16,712 | **IM 机器人框架**（HLZD 日报助手作为插件）|
| 🏆 **ActivityWatch/activitywatch** | 18,136 | **Event/Bucket 数据模型**（活动聚合）|
| 🏆 **Inbox Zero** | 11,550 | **Pydantic 结构化输出** |
| AstrBotDevs/AstrBot | 35,910 | AI Agent + IM（参考）|

---

## 核心能力矩阵

| 能力 | 实现 | 数据源 |
|---|---|---|
| **每日 18:00 自动触发** | Panmira scheduler | LangBot 调度器 |
| **邮件活动聚合** | imap_tools 拉取（HLZD-询盘响应 skill）| 网易/Gmail/Outlook IMAP |
| **IM 对话聚合** | 飞书 API（LangBot 飞书适配器）| 飞书 IM 历史 |
| **订单系统聚合** | HLZD-智能报价 + HLZD-物流装箱 skill | SQLite |
| **客户互动聚合** | HLZD-客户画像 skill（v0.2）| SQLite |
| **早会总结生成** | 从昨日日报 → to do list | 飞书多维表格 |
| **风险提醒** | SLA 临近 + 客户投诉 + 危险品 | 多 skill 联动 |
| **飞书卡片推送** | card-renderer | LangBot 飞书 |
| **一键提交主管** | 飞书卡片按钮 | 飞书 API |

---

## 工作流 v0.1

```
每日 18:00（Panmira scheduler）
  ↓
[1] LangBot 飞书适配器接收 trigger
  ↓
[2] HLZD-日报助手插件启动
  ↓
[3] 拉取 4 大数据源（并行）
  ├─ 邮件: HLZD-询盘响应 skill（imap_tools 拉取今日询盘）
  ├─ IM: 飞书 API 拉取今日对话
  ├─ 订单: SQLite 查 HLZD-智能报价/物流装箱 今日记录
  └─ 客户: SQLite 查 HLZD-客户画像 今日互动
  ↓
[4] 数据归一化 → Event Stream（借鉴 ActivityWatch）
  ↓
[5] LLM 生成日报结构（Claude + Pydantic schema）
  ↓
[6] 飞书卡片渲染（card-renderer）
  ↓
[7] 业务员一键确认/编辑/提交
  ↓
[8] 提交后写入飞书多维表格（主管 dashboard）
  ↓
[9] 早会总结自动生成（次日 8:00）
  - 昨日日报
  - to do list 完成度
  - 今日待办
```

---

## HLZD 日报结构（Pydantic schema）

```python
# scripts/daily_report_schema.py

from pydantic import BaseModel, Field
from typing import Literal
from datetime import date

class InquiryStats(BaseModel):
    """今日询盘统计"""
    total: int = Field(description="今日询盘总数")
    by_grade: dict[str, int] = Field(description="按 A/B/C 分级数量")
    by_category: dict[str, int] = Field(description="按 4 类分类数量")
    replied: int = Field(description="已回复数量")
    pending: int = Field(description="待回复数量")
    sla_breached: int = Field(description="SLA 临近/超期数量")

class QuoteStats(BaseModel):
    """今日报价统计"""
    total: int = Field(description="今日报价总数")
    sent: int = Field(description="已发送数量")
    draft: int = Field(description="草稿数量")
    framework_quotes: int = Field(description="快速框架报价数量")
    by_incoterm: dict[str, int] = Field(description="按 INCOTERMS 分布")
    by_currency: dict[str, int] = Field(description="按币种分布")

class ShipmentStats(BaseModel):
    """今日装箱统计"""
    total_orders: int = Field(description="今日装箱订单数")
    total_volume_m3: float = Field(description="总体积")
    avg_utilization: float = Field(description="平均体积利用率")
    containers_used: dict[str, int] = Field(description="按集装箱型号分布")
    hazmat_count: int = Field(description="危险品订单数")

class CustomerInteraction(BaseModel):
    """客户互动统计"""
    a_customers_contacted: int
    b_customers_contacted: int
    new_customers: int
    complaints: int
    pending_followups: int

class TodoItem(BaseModel):
    """待办事项"""
    priority: Literal["P0", "P1", "P2", "P3"]
    description: str
    customer_id: Optional[str] = None
    deadline: Optional[datetime] = None
    reason: str

class RiskAlert(BaseModel):
    """风险提醒"""
    type: Literal["SLA", "COMPLAINT", "HAZMAT", "SANCTION"]
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    description: str
    action_required: str

class MorningStandupSummary(BaseModel):
    """早会总结（次日 8:00 输出）"""
    yesterday_completed: list[str]  # 昨日日报中完成的 to do
    yesterday_pending: list[str]  # 昨日未完成
    today_priorities: list[TodoItem]  # 今日重点
    today_blockers: list[str]  # 今日阻塞

class DailyReport(BaseModel):
    """HLZD 日报主结构"""
    sales_id: str
    date: date
    inquiry_stats: InquiryStats
    quote_stats: QuoteStats
    shipment_stats: ShipmentStats
    customer_interaction: CustomerInteraction
    todos: list[TodoItem]
    risks: list[RiskAlert]
    achievements: list[str]
    next_day_plan: list[str]

    # 借鉴 Inbox Zero：结构化输出验证
    confidence: float = Field(ge=0.0, le=1.0)
    data_completeness: float = Field(description="数据完整度 0-1")
```

---

## scripts/ 设计 v0.1

```
scripts/
├── langbot_plugin.py              # ⭐ v0.1: HLZD 日报助手作为 LangBot 插件
├── daily_report_schema.py          # ⭐ v0.1: Pydantic 日报结构
├── event_collector.py             # ⭐ v0.1: 4 大数据源活动聚合（借鉴 ActivityWatch）
├── llm_summarizer.py              # ⭐ v0.1: LLM 生成日报结构
├── morning_standup.py             # ⭐ v0.1: 早会总结生成
├── feishu_card_renderer.py        # ⭐ v0.1: 飞书卡片渲染
├── feishu_bit_table_writer.py     # ⭐ v0.1: 飞书多维表格写入
├── data_normalizer.py             # ⭐ v0.1: 4 大数据源归一化为 Event Stream
├── orchestrator.py                # ⭐ v0.1: 主调度
└── scheduler.py                   # ⭐ v0.1: 每日 18:00 自动触发
```

---

## scripts/event_collector.py 设计

```python
"""
HLZD 日报助手 - 活动数据收集器
借鉴 ActivityWatch Event/Bucket 数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Literal
import asyncio

@dataclass
class ActivityEvent:
    """借鉴 ActivityWatch Event 数据模型"""
    timestamp: datetime
    duration: int  # seconds
    bucket: Literal["email", "im", "order", "customer"]
    data: dict
    sales_id: str

    # 借鉴 ActivityWatch heartbeat merge
    @classmethod
    def merge(cls, e1: "ActivityEvent", e2: "ActivityEvent") -> "ActivityEvent":
        """心跳合并：相同数据 + 在 pulsetime 内 → 合并"""
        if (e1.bucket == e2.bucket and 
            e1.data == e2.data and 
            (e2.timestamp - e1.timestamp).total_seconds() < 300):  # 5 分钟 pulsetime
            return ActivityEvent(
                timestamp=e1.timestamp,
                duration=e1.duration + e2.duration,
                bucket=e1.bucket,
                data=e1.data,
                sales_id=e1.sales_id,
            )
        return e2


class EventCollector:
    """4 大数据源活动聚合"""

    async def collect_today(self, sales_id: str, date: date) -> list[ActivityEvent]:
        """异步拉取 4 大数据源"""

        # 借鉴 ActivityWatch aw-watcher 设计
        tasks = [
            self._collect_email_events(sales_id, date),
            self._collect_im_events(sales_id, date),
            self._collect_order_events(sales_id, date),
            self._collect_customer_events(sales_id, date),
        ]
        results = await asyncio.gather(*tasks)
        
        all_events = []
        for events in results:
            all_events.extend(events)
        
        # 心跳合并
        return self._merge_events(all_events)

    async def _collect_email_events(self, sales_id: str, date: date) -> list[ActivityEvent]:
        """邮件事件（HLZD-询盘响应 skill）"""
        # 调用 HLZD-询盘响应 skill 拉今日询盘
        from hlzd_inquiry_response import InquiryResponse
        inquiries = await InquiryResponse.fetch_today_inquiries(sales_id, date)
        return [
            ActivityEvent(
                timestamp=inq.received_at,
                duration=0,  # 邮件事件 duration 用 0
                bucket="email",
                data={
                    "type": "inquiry_received",
                    "inquiry_id": inq.id,
                    "sender": inq.sender,
                    "category": inq.category,  # QUOTE_REQUEST/LOGISTICS/AFTER_SALE/SPAM
                    "grade": inq.customer_grade,  # A/B/C
                    "status": inq.status,  # DRAFTED/SENT/REPLIED
                },
                sales_id=sales_id,
            )
            for inq in inquiries
        ]

    async def _collect_im_events(self, sales_id: str, date: date) -> list[ActivityEvent]:
        """IM 对话事件（飞书 API）"""
        # 借鉴 LangBot 飞书适配器
        from langbot.platforms.feishu import FeishuAdapter
        adapter = FeishuAdapter(sales_id)
        chats = await adapter.get_today_chats(date)
        return [
            ActivityEvent(
                timestamp=chat.start_time,
                duration=chat.duration_seconds,
                bucket="im",
                data={
                    "type": "chat",
                    "chat_id": chat.id,
                    "participants": chat.participants,
                    "message_count": chat.message_count,
                },
                sales_id=sales_id,
            )
            for chat in chats
        ]

    async def _collect_order_events(self, sales_id: str, date: date) -> list[ActivityEvent]:
        """订单事件（HLZD-智能报价 + HLZD-物流装箱）"""
        # 调用 HLZD-智能报价 skill 拉今日报价
        from hlzd_smart_quote import SmartQuote
        quotes = await SmartQuote.fetch_today_quotes(sales_id, date)
        # 调用 HLZD-物流装箱 skill 拉今日装箱
        from hlzd_shipment import Shipment
        shipments = await Shipment.fetch_today_shipments(sales_id, date)

        events = []
        for q in quotes:
            events.append(ActivityEvent(
                timestamp=q.created_at,
                duration=0,
                bucket="order",
                data={
                    "type": "quote",
                    "quote_id": q.id,
                    "amount": q.amount,
                    "currency": q.currency,
                    "incoterm": q.incoterm,
                    "status": q.status,
                },
                sales_id=sales_id,
            ))
        for s in shipments:
            events.append(ActivityEvent(
                timestamp=s.created_at,
                duration=0,
                bucket="order",
                data={
                    "type": "shipment",
                    "shipment_id": s.id,
                    "container_type": s.container_type,
                    "volume_utilization": s.volume_utilization,
                    "is_hazmat": s.is_hazmat,
                },
                sales_id=sales_id,
            ))
        return events

    async def _collect_customer_events(self, sales_id: str, date: date) -> list[ActivityEvent]:
        """客户互动事件（HLZD-客户画像）"""
        from hlzd_customer_persona import CustomerPersona
        interactions = await CustomerPersona.fetch_today_interactions(sales_id, date)
        return [
            ActivityEvent(
                timestamp=inter.timestamp,
                duration=0,
                bucket="customer",
                data={
                    "type": "interaction",
                    "customer_id": inter.customer_id,
                    "customer_grade": inter.customer_grade,
                    "interaction_type": inter.type,  # email/im/call
                    "summary": inter.summary,
                },
                sales_id=sales_id,
            )
            for inter in interactions
        ]

    def _merge_events(self, events: list[ActivityEvent]) -> list[ActivityEvent]:
        """心跳合并（借鉴 ActivityWatch）"""
        if not events:
            return []
        events.sort(key=lambda e: e.timestamp)
        merged = [events[0]]
        for e in events[1:]:
            last = merged[-1]
            if last.bucket == e.bucket and last.data == e.data:
                merged[-1] = ActivityEvent.merge(last, e)
            else:
                merged.append(e)
        return merged
```

---

## scripts/llm_summarizer.py 设计

```python
"""
HLZD 日报助手 - LLM 摘要生成器
借鉴 Inbox Zero Zod schema + Pydantic 验证
"""
from daily_report_schema import DailyReport
from event_collector import ActivityEvent, EventCollector

class LLMSummarizer:
    """LLM 生成日报结构"""

    async def generate_report(self, sales_id: str, date: str) -> DailyReport:
        """LLM 摘要生成（带 Pydantic 验证）"""

        # 1. 收集事件
        events = await EventCollector().collect_today(sales_id, date)

        # 2. 准备 LLM prompt
        events_text = self._format_events(events)
        prompt = f"""请基于以下活动数据生成 HLZD 业务员日报：

# 活动数据
{events_text}

# 输出格式（必须严格遵守）
请输出 JSON，符合以下结构:
{{
  "sales_id": "{sales_id}",
  "date": "{date}",
  "inquiry_stats": {{ ... }},
  "quote_stats": {{ ... }},
  ...
}}

# 要求
1. 数字必须与活动数据一致
2. 风险提醒基于 SLA 临近 + 客户投诉 + 危险品
3. 待办事项按优先级排序（P0 最高）
4. 早会总结简洁（≤ 200 字）
"""

        # 3. 调用 LLM（Claude）
        from langbot.provider.runners import ClaudeRunner
        response = await ClaudeRunner.generate(
            prompt=prompt,
            response_schema=DailyReport,  # 借鉴 Inbox Zero Zod：强制 schema
            model="claude-sonnet-4.6",
        )

        # 4. Pydantic 自动验证（借鉴 Inbox Zero）
        try:
            report = DailyReport.parse_raw(response)
        except ValidationError as e:
            # 验证失败 → 自动重试或 fallback
            raise LLMOutputError(f"Pydantic 验证失败: {e}")

        return report

    def _format_events(self, events: list[ActivityEvent]) -> str:
        """格式化为 LLM 可读文本"""
        lines = []
        for e in events:
            lines.append(f"[{e.timestamp}] [{e.bucket}] {e.data}")
        return "\n".join(lines)
```

---

## 飞书卡片设计

---

## 更多细节

完整设计文档（v0.1.x 实现细节 + 错误地图 + 性能目标）见 [references/deep-dive.md](references/deep-dive.md)。
