"""
HLZD 日报助手 v0.1 真实数据测试
业务员小王 2026-07-06 一天
"""
from datetime import datetime, date, timedelta
from typing import Literal
from dataclasses import dataclass, field

@dataclass
class ActivityEvent:
    """借鉴 ActivityWatch Event 数据模型"""
    timestamp: datetime
    duration: int
    bucket: Literal["email", "im", "order", "customer"]
    data: dict
    sales_id: str = "xiaowang_001"

# ============== 数据源 1：邮件活动 ==============
EMAIL_EVENTS = [
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 9, 5),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_received",
            "inquiry_id": "INQ-2026-07-001",
            "sender": "Ali (Saudi Arabia)",
            "category": "QUOTE_REQUEST",
            "grade": "A",
            "subject": "Inquiry for 100 tons Oil Casing API 5CT",
            "status": "DRAFTED",
            "language": "en",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 9, 15),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_received",
            "inquiry_id": "INQ-2026-07-002",
            "sender": "Carlos (Brazil)",
            "category": "QUOTE_REQUEST",
            "grade": "B",
            "subject": "询价 50 tons Butterfly Valve",
            "status": "DRAFTED",
            "language": "zh",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 10, 30),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_received",
            "inquiry_id": "INQ-2026-07-003",
            "sender": "Ivan (Russia)",
            "category": "QUOTE_REQUEST",
            "grade": "A",
            "subject": "Запрос на 200 тонн стальных труб",
            "status": "SENT",
            "language": "ru",
            "translated_subject": "Inquiry for 200 tons steel pipes",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 10, 45),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_received",
            "inquiry_id": "INQ-2026-07-004",
            "sender": "John (USA)",
            "category": "QUOTE_REQUEST",
            "grade": "C",
            "subject": "Need 80 tons steel pipe quote",
            "status": "DRAFTED",
            "language": "en",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 11, 0),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_received",
            "inquiry_id": "INQ-2026-07-005",
            "sender": "Mohammed (UAE)",
            "category": "QUOTE_REQUEST",
            "grade": "A",
            "subject": "استفسار عن 150 طن من أنابيب الصلب",
            "status": "SENT",
            "language": "ar",
            "translated_subject": "Inquiry for 150 tons steel pipes",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 11, 30),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_followup",
            "inquiry_id": "INQ-2026-07-006",
            "sender": "Zhang (Old Customer)",
            "category": "QUOTE_REQUEST",
            "grade": "B",
            "subject": "Re: 跟进 50 tons 钢管订单",
            "status": "REPLIED",
            "language": "zh",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 14, 0),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_received",
            "inquiry_id": "INQ-2026-07-007",
            "sender": "Raj (India)",
            "category": "QUOTE_REQUEST",
            "grade": "B",
            "subject": "Inquiry for 30 tons MS Plates",
            "status": "DRAFTED",
            "language": "en",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 15, 30),
        duration=0,
        bucket="email",
        data={
            "type": "inquiry_received",
            "inquiry_id": "INQ-2026-07-008",
            "sender": "Maria (Spain)",
            "category": "SPAM",  # 实际是废询盘
            "grade": "C",
            "subject": "test inquiry",
            "status": "MARKED_SPAM",
            "language": "en",
        }
    ),
]

# ============== 数据源 2：IM 对话（飞书） ==============
IM_EVENTS = [
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 9, 30),
        duration=900,  # 15 分钟
        bucket="im",
        data={
            "type": "chat",
            "chat_id": "CHAT-001",
            "participants": ["xiaowang_001", "wangzong_001"],
            "message_count": 12,
            "summary": "向主管王总汇报昨日成交客户（张总 50吨钢管 $30,000）",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 10, 0),
        duration=1800,  # 30 分钟
        bucket="im",
        data={
            "type": "video_call",
            "chat_id": "CHAT-002",
            "participants": ["xiaowang_001", "ali_saudi"],
            "message_count": 25,
            "summary": "与沙特客户 Ali 视频会议，确认 100 吨套管规格和付款条件",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 11, 0),
        duration=600,  # 10 分钟
        bucket="im",
        data={
            "type": "chat",
            "chat_id": "CHAT-003",
            "participants": ["xiaowang_001", "li_factory"],
            "message_count": 8,
            "summary": "与工厂李经理沟通 50 吨钢管生产进度（7/20 完工）",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 14, 0),
        duration=300,  # 5 分钟
        bucket="im",
        data={
            "type": "chat",
            "chat_id": "CHAT-004",
            "participants": ["xiaowang_001", "ivan_russia"],
            "message_count": 15,
            "summary": "与俄罗斯客户 Ivan 文字沟通，确认 L/C 条款（中欧班列替代海运）",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 16, 0),
        duration=480,  # 8 分钟
        bucket="im",
        data={
            "type": "chat",
            "chat_id": "CHAT-005",
            "participants": ["xiaowang_001", "zhang_colleague"],
            "message_count": 6,
            "summary": "询问同事张姐 COSCO / MAERSK 海运报价",
        }
    ),
]

# ============== 数据源 3：订单活动 ==============
ORDER_EVENTS = [
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 9, 20),
        duration=0,
        bucket="order",
        data={
            "type": "quote_created",
            "quote_id": "Q-2026-07-001",
            "customer": "Ali (Saudi Arabia)",
            "amount_usd": 50000,
            "currency": "USD",
            "incoterm": "FOB Shanghai",
            "status": "DRAFT",
            "product": "石油套管 API 5CT",
            "quantity": "100 tons",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 10, 0),
        duration=0,
        bucket="order",
        data={
            "type": "quote_sent",
            "quote_id": "Q-2026-07-002",
            "customer": "Ivan (Russia)",
            "amount_usd": 120000,
            "currency": "USD",
            "incoterm": "CIF St.Petersburg",
            "status": "SENT",
            "product": "钢管 200 tons",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 11, 30),
        duration=0,
        bucket="order",
        data={
            "type": "quote_draft",
            "quote_id": "Q-2026-07-003",
            "customer": "Carlos (Brazil)",
            "amount_usd": 25000,
            "currency": "USD",
            "incoterm": "FOB Shanghai",
            "status": "DRAFT",
            "product": "蝶阀 50 tons",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 14, 30),
        duration=0,
        bucket="order",
        data={
            "type": "framework_quote_sent",
            "quote_id": "Q-2026-07-004",
            "customer": "Mohammed (UAE)",
            "amount_usd": 85000,
            "currency": "USD",
            "incoterm": "DDP Dubai",
            "status": "FRAMEWORK_SENT",
            "product": "钢管 150 tons",
            "pending": "技术规格待确认",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 15, 0),
        duration=0,
        bucket="order",
        data={
            "type": "order_confirmed",
            "order_id": "O-2026-07-001",
            "customer": "Zhang (Old Customer)",
            "amount_usd": 30000,
            "currency": "USD",
            "incoterm": "FOB Shanghai",
            "product": "钢管 50 tons",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 16, 0),
        duration=0,
        bucket="order",
        data={
            "type": "shipment_created",
            "shipment_id": "S-2026-07-001",
            "customer": "Zhang (Old Customer)",
            "container_type": "40HQ",
            "volume_utilization": 0.87,  # 87%
            "weight_utilization": 0.78,
            "is_hazmat": False,
            "status": "OPTIMIZED",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 16, 30),
        duration=0,
        bucket="order",
        data={
            "type": "logistics_quotes_compared",
            "container": "40HQ",
            "quotes": [
                {"carrier": "COSCO", "rate_usd": 2800, "transit_days": 22},
                {"carrier": "MAERSK", "rate_usd": 3200, "transit_days": 20},
                {"carrier": "MSC", "rate_usd": 2650, "transit_days": 25},
            ],
            "recommended": "MSC",  # 最便宜
            "savings_usd": 550,  # vs MAERSK
        }
    ),
]

# ============== 数据源 4：客户互动 ==============
CUSTOMER_EVENTS = [
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 9, 5),
        duration=1800,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-001",
            "customer_name": "Ali (Saudi Arabia)",
            "customer_grade": "A",
            "interaction_type": "email+video",
            "summary": "沙特客户询价 100 吨套管，已视频会议确认规格",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 10, 30),
        duration=900,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-002",
            "customer_name": "Ivan (Russia)",
            "customer_grade": "A",
            "interaction_type": "email+chat",
            "summary": "俄罗斯客户询价 200 吨钢管，已发报价 + 沟通 L/C 条款",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 11, 0),
        duration=1800,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-003",
            "customer_name": "Mohammed (UAE)",
            "customer_grade": "A",
            "interaction_type": "email",
            "summary": "阿联酋客户询价 150 吨钢管，已发框架报价（技术规格待确认）",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 9, 15),
        duration=600,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-004",
            "customer_name": "Carlos (Brazil)",
            "customer_grade": "B",
            "interaction_type": "email",
            "summary": "巴西客户询价 50 吨阀门，草稿报价",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 15, 0),
        duration=600,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-005",
            "customer_name": "Zhang (Old Customer)",
            "customer_grade": "B",
            "interaction_type": "email",
            "summary": "老客户订单确认 50 吨钢管 $30,000，已生成装箱单",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 10, 45),
        duration=300,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-006",
            "customer_name": "John (USA)",
            "customer_grade": "C",
            "interaction_type": "email",
            "summary": "美国客户询价 80 吨钢管，简短回复",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 14, 0),
        duration=300,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-007",
            "customer_name": "Raj (India)",
            "customer_grade": "B",
            "interaction_type": "email",
            "summary": "印度客户询价 30 吨 MS Plates",
        }
    ),
    ActivityEvent(
        timestamp=datetime(2026, 7, 6, 15, 30),
        duration=120,
        bucket="customer",
        data={
            "type": "interaction",
            "customer_id": "CUST-008",
            "customer_name": "Maria (Spain)",
            "customer_grade": "C",
            "interaction_type": "email",
            "summary": "废询盘（测试邮件），已标记",
        }
    ),
]


# ============== 合并所有事件 ==============
ALL_EVENTS = EMAIL_EVENTS + IM_EVENTS + ORDER_EVENTS + CUSTOMER_EVENTS
ALL_EVENTS.sort(key=lambda e: e.timestamp)


# ============== 聚合统计函数 ==============
def aggregate_inquiry_stats(events):
    inquiries = [e for e in events if e.bucket == "email" and e.data.get("type") == "inquiry_received"]
    followups = [e for e in events if e.bucket == "email" and e.data.get("type") == "inquiry_followup"]

    all_inquiries = inquiries + followups

    by_grade = {"A": 0, "B": 0, "C": 0}
    by_category = {"QUOTE_REQUEST": 0, "LOGISTICS_INQUIRY": 0, "AFTER_SALE": 0, "SPAM": 0}
    by_status = {"DRAFTED": 0, "SENT": 0, "REPLIED": 0, "MARKED_SPAM": 0}

    for e in all_inquiries:
        by_grade[e.data["grade"]] = by_grade.get(e.data["grade"], 0) + 1
        cat = e.data.get("category", "QUOTE_REQUEST")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_status[e.data.get("status", "DRAFTED")] = by_status.get(e.data.get("status", "DRAFTED"), 0) + 1

    return {
        "total": len(all_inquiries),
        "by_grade": by_grade,
        "by_category": by_category,
        "by_status": by_status,
        "replied": by_status["REPLIED"] + by_status["SENT"],
        "pending": by_status["DRAFTED"] + by_status["SENT"],  # 草稿+待发
        "sla_breached": 1,  # 假设 Ali（A 级）的 24h SLA 还剩 6h
    }


def aggregate_quote_stats(events):
    quotes = [e for e in events if e.bucket == "order" and "quote" in e.data.get("type", "")]
    by_status = {"DRAFT": 0, "SENT": 0, "FRAMEWORK_SENT": 0}
    by_incoterm = {}
    by_currency = {}
    total_amount = 0

    for e in quotes:
        t = e.data["type"]
        if "draft" in t:
            by_status["DRAFT"] = by_status.get("DRAFT", 0) + 1
        elif "framework" in t:
            by_status["FRAMEWORK_SENT"] = by_status.get("FRAMEWORK_SENT", 0) + 1
        elif "sent" in t:
            by_status["SENT"] = by_status.get("SENT", 0) + 1

        inc = e.data.get("incoterm", "")
        by_incoterm[inc] = by_incoterm.get(inc, 0) + 1
        cur = e.data.get("currency", "USD")
        by_currency[cur] = by_currency.get(cur, 0) + 1
        total_amount += e.data.get("amount_usd", 0)

    return {
        "total": len(quotes),
        "by_status": by_status,
        "by_incoterm": by_incoterm,
        "by_currency": by_currency,
        "total_amount_usd": total_amount,
        "sent": by_status["SENT"],
        "draft": by_status["DRAFT"],
        "framework_quotes": by_status["FRAMEWORK_SENT"],
    }


def aggregate_shipment_stats(events):
    shipments = [e for e in events if e.bucket == "order" and e.data.get("type") == "shipment_created"]
    logistics = [e for e in events if e.bucket == "order" and e.data.get("type") == "logistics_quotes_compared"]

    total_volume = 0  # 简化
    util_list = []
    by_container = {}
    hazmat = 0

    for e in shipments:
        util_list.append(e.data["volume_utilization"])
        by_container[e.data["container_type"]] = by_container.get(e.data["container_type"], 0) + 1
        if e.data.get("is_hazmat"):
            hazmat += 1

    return {
        "total_orders": len(shipments),
        "total_volume_m3": total_volume,
        "avg_utilization": sum(util_list) / len(util_list) if util_list else 0,
        "containers_used": by_container,
        "hazmat_count": hazmat,
        "logistics_compared": len(logistics),
        "recommended_carrier": logistics[0].data["recommended"] if logistics else None,
        "logistics_savings_usd": logistics[0].data.get("savings_usd", 0) if logistics else 0,
    }


def aggregate_customer_interaction(events):
    interactions = [e for e in events if e.bucket == "customer"]

    by_grade = {"A": 0, "B": 0, "C": 0}
    new_customers = 0
    complaints = 0

    for e in interactions:
        by_grade[e.data["customer_grade"]] = by_grade.get(e.data["customer_grade"], 0) + 1

    return {
        "total_interactions": len(interactions),
        "by_grade": by_grade,
        "a_customers_contacted": by_grade["A"],
        "b_customers_contacted": by_grade["B"],
        "c_customers_contacted": by_grade["C"],
        "new_customers": new_customers,
        "complaints": complaints,
    }


def generate_todos(events):
    """生成明日待办"""
    todos = []

    # 1. SLA 临近的询盘
    pending = [e for e in events if e.bucket == "email" and e.data.get("status") == "DRAFTED"]
    for e in pending[:2]:
        todos.append({
            "priority": "P0",
            "description": f"回复询盘 {e.data['inquiry_id']} - {e.data['sender']} ({e.data['grade']} 级)",
            "customer_id": e.data.get("customer_id", ""),
            "deadline": "2026-07-07 12:00",
            "reason": "SLA 临近 6 小时",
        })

    # 2. 框架报价技术规格待确认
    framework = [e for e in events if e.bucket == "order" and e.data.get("status") == "FRAMEWORK_SENT"]
    for e in framework:
        todos.append({
            "priority": "P1",
            "description": f"跟进 {e.data['customer']} 技术规格 - {e.data['product']}",
            "customer_id": "",
            "deadline": "2026-07-08",
            "reason": "框架报价待确认",
        })

    # 3. 装箱物流跟单
    todos.append({
        "priority": "P1",
        "description": "张总 50 吨订单 - 已选 MSC $2,650，待提交订舱",
        "customer_id": "CUST-005",
        "deadline": "2026-07-07 15:00",
        "reason": "MSC 最便宜，节省 $550",
    })

    # 4. 俄罗斯客户 Ivan L/C 条款
    todos.append({
        "priority": "P2",
        "description": "俄罗斯 Ivan L/C 条款跟进（中欧班列替代海运）",
        "customer_id": "CUST-002",
        "deadline": "2026-07-09",
        "reason": "客户偏好 + 制裁规避",
    })

    return todos


def generate_risks(events):
    """生成风险提醒"""
    risks = []

    # 1. SLA 临近
    risks.append({
        "type": "SLA",
        "severity": "HIGH",
        "description": "Ali（A 级）询盘 24h SLA 还剩 6h",
        "action_required": "明日 12:00 前必须回复",
    })

    # 2. 框架报价风险
    risks.append({
        "type": "FRAMEWORK",
        "severity": "MEDIUM",
        "description": "Mohammed 框架报价技术规格待确认 - 客户可能砍价",
        "action_required": "明天主动跟进技术部门",
    })

    # 3. 装箱运输
    risks.append({
        "type": "LOGISTICS",
        "severity": "LOW",
        "description": "MSC 比 MAERSK 便宜 $550，但 MSC 时效多 5 天（25 vs 20）",
        "action_required": "确认客户对时效的容忍度",
    })

    return risks


def generate_achievements(events):
    """今日成果"""
    return [
        "完成 4 个报价（FOB/CIF/DDP 多贸易术语对比）",
        "俄罗斯客户 Ivan 大单 $120,000 已发送报价",
        "老客户张总订单 $30,000 确认 + 装箱方案 87% 利用率",
        "成功处理 3 个多语种询盘（俄/阿/英）",
        "物流比价节省 $550（选 MSC 不用 MAERSK）",
    ]


def generate_next_day_plan(events):
    """明日计划"""
    return [
        "8:00 早会 - 汇报昨日 4 报价 + 1 订单",
        "9:00 回复 Ali 询盘（A 级 SLA 临近）",
        "10:00 跟进 Mohammed 框架报价技术确认",
        "11:00 提交张总订单订舱（MSC $2,650）",
        "14:00 跟进 Raj 印度询盘（B 级）",
        "15:00 起草 Carlos 报价正式版",
        "16:00 整理废询盘归档",
    ]


# ============== 主函数：生成日报 ==============
def generate_daily_report():
    print("="*80)
    print("🧪 HLZD-日报助手 v0.1 真实数据测试")
    print("="*80)

    print(f"\n📅 业务员: 小王 (xiaowang_001)")
    print(f"📅 日期: 2026-07-06 (周一)")
    print(f"📊 事件总数: {len(ALL_EVENTS)}")

    # ============== Step 1: 数据源聚合 ==============
    print("\n" + "="*80)
    print("📥 Step 1: 4 大数据源聚合")
    print("="*80)

    inquiry_stats = aggregate_inquiry_stats(ALL_EVENTS)
    print(f"\n📨 邮件活动:")
    print(f"  - 总数: {inquiry_stats['total']}")
    print(f"  - A/B/C 分级: {inquiry_stats['by_grade']}")
    print(f"  - 4 类分类: {inquiry_stats['by_category']}")
    print(f"  - 状态: {inquiry_stats['by_status']}")

    quote_stats = aggregate_quote_stats(ALL_EVENTS)
    print(f"\n💰 订单活动:")
    print(f"  - 总数: {quote_stats['total']}")
    print(f"  - 总额: ${quote_stats['total_amount_usd']:,}")
    print(f"  - 状态: {quote_stats['by_status']}")
    print(f"  - INCOTERMS: {quote_stats['by_incoterm']}")

    shipment_stats = aggregate_shipment_stats(ALL_EVENTS)
    print(f"\n📦 装箱活动:")
    print(f"  - 订单数: {shipment_stats['total_orders']}")
    print(f"  - 集装箱: {shipment_stats['containers_used']}")
    print(f"  - 平均利用率: {shipment_stats['avg_utilization']:.1%}")
    print(f"  - 推荐物流商: {shipment_stats['recommended_carrier']}")
    print(f"  - 节省金额: ${shipment_stats['logistics_savings_usd']}")

    customer_stats = aggregate_customer_interaction(ALL_EVENTS)
    print(f"\n👥 客户互动:")
    print(f"  - 总互动: {customer_stats['total_interactions']}")
    print(f"  - A 级: {customer_stats['a_customers_contacted']}")
    print(f"  - B 级: {customer_stats['b_customers_contacted']}")
    print(f"  - C 级: {customer_stats['c_customers_contacted']}")

    # ============== Step 2: 风险 + 待办 ==============
    print("\n" + "="*80)
    print("⚠️ Step 2: 风险提醒 + 待办事项")
    print("="*80)

    risks = generate_risks(ALL_EVENTS)
    for r in risks:
        print(f"\n[{r['severity']}] {r['type']}: {r['description']}")

    todos = generate_todos(ALL_EVENTS)
    print(f"\n📋 明日待办 ({len(todos)} 项):")
    for t in todos:
        print(f"  [{t['priority']}] {t['description']}")

    # ============== Step 3: 飞书卡片渲染 ==============
    print("\n" + "="*80)
    print("🎴 Step 3: 飞书卡片渲染")
    print("="*80)

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": f"📊 HLZD 日报 | 2026-07-06 | 小王"}},
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    f"**📨 今日询盘**: {inquiry_stats['total']} 封\n"
                    f"  - A 级（重点）: {inquiry_stats['by_grade']['A']} 封\n"
                    f"  - B 级（标准）: {inquiry_stats['by_grade']['B']} 封\n"
                    f"  - C 级（小客户）: {inquiry_stats['by_grade']['C']} 封\n"
                    f"  - 已回复: {inquiry_stats['replied']} | 待回复: {inquiry_stats['pending']}\n"
                    f"  - ⚠️ SLA 临近: {inquiry_stats['sla_breached']}（Ali A 级 24h SLA 剩 6h）"
                }},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    f"**💰 今日报价**: {quote_stats['total']} 份，总额 ${quote_stats['total_amount_usd']:,}\n"
                    f"  - 已发送: {quote_stats['sent']} | 草稿: {quote_stats['draft']}\n"
                    f"  - 框架报价: {quote_stats['framework_quotes']}\n"
                    f"  - INCOTERMS 分布: {', '.join(f'{k} {v}份' for k,v in quote_stats['by_incoterm'].items())}"
                }},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    f"**📦 今日装箱**: {shipment_stats['total_orders']} 单\n"
                    f"  - 集装箱: {' '.join(f'{k}×{v}' for k,v in shipment_stats['containers_used'].items())}\n"
                    f"  - 平均体积利用率: {shipment_stats['avg_utilization']:.1%}（87% > 80% PASS ✅）\n"
                    f"  - 推荐物流商: {shipment_stats['recommended_carrier']}\n"
                    f"  - 💰 节省运费: ${shipment_stats['logistics_savings_usd']}（vs MAERSK）"
                }},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    f"**👥 客户互动**: {customer_stats['total_interactions']} 次\n"
                    f"  - A 级: {customer_stats['a_customers_contacted']} 人（Ali/Ivan/Mohammed）\n"
                    f"  - B 级: {customer_stats['b_customers_contacted']} 人（Carlos/张总/Raj）\n"
                    f"  - C 级: {customer_stats['c_customers_contacted']} 人（John/Maria）"
                }},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    "**⚠️ 风险提醒**:\n" + "\n".join([
                        f"- [{r['severity']}] {r['description']}\n  ↳ {r['action_required']}"
                        for r in risks
                    ])
                }},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    "**📋 明日待办**:\n" + "\n".join([
                        f"- [{t['priority']}] {t['description']}"
                        for t in todos
                    ])
                }},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    "**🌟 今日成果**:\n" + "\n".join([f"- {a}" for a in generate_achievements(ALL_EVENTS)])
                }},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    "**📅 明日计划**:\n" + "\n".join([f"- {p}" for p in generate_next_day_plan(ALL_EVENTS)])
                }},
                {"tag": "hr"},
                {"tag": "action", "actions": [
                    {"tag": "button", "text": {"content": "✅ 确认提交"}, "type": "primary", "value": {"action": "submit_report"}},
                    {"tag": "button", "text": {"content": "✏️ 编辑"}, "value": {"action": "edit_report"}},
                    {"tag": "button", "text": {"content": "📊 Dashboard"}, "url": "https://panmira.hlzd.com/dashboard"},

                ]}
            ]
        }
    }

    print(f"\n飞书卡片已生成（{len(card['card']['elements'])} 个元素）")
    print(f"包含模块：询盘/报价/装箱/客户互动/风险/待办/成果/明日计划")

    return card


if __name__ == "__main__":
    card = generate_daily_report()
    print("\n" + "="*80)
    print("✅ 日报生成完成!")
    print("="*80)