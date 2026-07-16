# hlzd-daily-report — Deep Dive

> 本文件收纳 SKILL.md 因 500 行约束移出的细节章节，仅供 deep-load 参考。


```python
# scripts/feishu_card_renderer.py

def render_daily_report_card(report: DailyReport) -> dict:
    """飞书卡片渲染（card-renderer）"""

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📊 HLZD 日报 | {report.date}"}
            },
            "elements": [
                # 询盘统计
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content":
                        f"**📨 今日询盘**: {report.inquiry_stats.total} 封\n"
                        f"  - A 级（重点）: {report.inquiry_stats.by_grade.get('A', 0)}\n"
                        f"  - B 级（标准）: {report.inquiry_stats.by_grade.get('B', 0)}\n"
                        f"  - C 级（小客户）: {report.inquiry_stats.by_grade.get('C', 0)}\n"
                        f"  - 已回复: {report.inquiry_stats.replied} | 待回复: {report.inquiry_stats.pending}\n"
                        f"  - ⚠️ SLA 临近: {report.inquiry_stats.sla_breached}"
                    }
                },
                {"tag": "hr"},
                # 报价统计
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content":
                        f"**💰 今日报价**: {report.quote_stats.total} 份\n"
                        f"  - 已发送: {report.quote_stats.sent} | 草稿: {report.quote_stats.draft}\n"
                        f"  - 框架报价: {report.quote_stats.framework_quotes}\n"
                        f"  - 币种分布: {', '.join(f'{k} {v}' for k,v in report.quote_stats.by_currency.items())}"
                    }
                },
                {"tag": "hr"},
                # 装箱统计
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content":
                        f"**📦 今日装箱**: {report.shipment_stats.total_orders} 单\n"
                        f"  - 总体积: {report.shipment_stats.total_volume_m3:.1f} m³\n"
                        f"  - 平均利用率: {report.shipment_stats.avg_utilization:.1%}\n"
                        f"  - 危险品: {report.shipment_stats.hazmat_count}"
                    }
                },
                {"tag": "hr"},
                # 风险提醒
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content":
                        "**⚠️ 风险提醒**:\n" + "\n".join([
                            f"- [{r.severity}] {r.description}" for r in report.risks
                        ])
                    }
                },
                {"tag": "hr"},
                # 待办事项
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content":
                        "**📋 明日待办**:\n" + "\n".join([
                            f"- [{t.priority}] {t.description}" for t in report.todos[:5]
                        ])
                    }
                },
                {"tag": "hr"},
                # 操作按钮
                {"tag": "action", "actions": [
                    {"tag": "button", "text": {"content": "✅ 确认提交"}, "type": "primary", "value": {"action": "submit_report"}},
                    {"tag": "button", "text": {"content": "✏️ 编辑"}, "value": {"action": "edit_report"}},
                    {"tag": "button", "text": {"content": "📊 查看 Dashboard"}, "url": "https://panmira.hlzd.com/dashboard"}},
                ]}
            ]
        }
    }
```

---

## LangBot 插件集成（v0.1 关键）

```python
# scripts/langbot_plugin.py
# HLZD 日报助手作为 LangBot 插件

from langbot_plugin import Plugin, Event

class HLZDDailyReportPlugin(Plugin):
    """HLZD 日报助手 LangBot 插件"""

    async def on_message(self, event: Event):
        """飞书消息事件"""
        text = event.message.text
        if text == "今日日报" or "生成日报" in text:
            report = await LLMSummarizer().generate_report(
                sales_id=event.user_id,
                date=event.message.create_time.date(),
            )
            card = render_daily_report_card(report)
            await event.reply(card)

    async def on_schedule(self, schedule_event):
        """定时任务（每日 18:00）"""
        for sales_id in self.get_active_sales():
            report = await LLMSummarizer().generate_report(
                sales_id=sales_id,
                date=date.today(),
            )
            card = render_daily_report_card(report)
            await self.send_to_user(sales_id, card)

    async def on_card_action(self, action_event):
        """飞书卡片按钮回调"""
        if action_event.value["action"] == "submit_report":
            # 写入飞书多维表格（主管 dashboard）
            await FeishuBitTableWriter.write_report(action_event.user_id, action_event.context)
            await action_event.reply("✅ 日报已提交，主管可在 Dashboard 查看")
```

---

## 早会总结生成（次日 8:00）

```python
# scripts/morning_standup.py

class MorningStandup:
    """早会总结生成（次日 8:00）"""

    async def generate(self, sales_id: str, date: date) -> MorningStandupSummary:
        """从昨日日报生成早会总结"""

        # 1. 拉取昨日日报
        yesterday_report = await DailyReportStore.fetch(sales_id, date - timedelta(days=1))

        # 2. 提取昨日 to do 完成度
        yesterday_todos = yesterday_report.todos
        completed = [t for t in yesterday_todos if t.status == "completed"]
        pending = [t for t in yesterday_todos if t.status == "pending"]

        # 3. 生成今日重点（基于客户互动 + SLA）
        today_priorities = await self._generate_today_priorities(sales_id, date)

        # 4. 生成今日阻塞
        blockers = await self._detect_blockers(sales_id, date)

        return MorningStandupSummary(
            yesterday_completed=[t.description for t in completed],
            yesterday_pending=[t.description for t in pending],
            today_priorities=today_priorities,
            today_blockers=blockers,
        )

    async def _detect_blockers(self, sales_id: str, date: date) -> list[str]:
        """检测今日阻塞"""
        blockers = []

        # 检查 SLA 临近的客户
        sla_customers = await CustomerPersona.fetch_sla_breaching(sales_id, date)
        if sla_customers:
            blockers.append(f"⚠️ {len(sla_customers)} 个客户 SLA 临近")

        # 检查待回询盘
        pending_inquiries = await InquiryResponse.fetch_pending(sales_id, date)
        if pending_inquiries:
            blockers.append(f"📬 {len(pending_inquiries)} 个询盘待回复")

        return blockers
```

---

## references/ 设计 v0.1

```
references/
├── langbot_plugin_dev.md           # ⭐ v0.1: LangBot 插件开发指南
├── activitywatch_data_model.md     # ⭐ v0.1: ActivityWatch Event/Bucket 模型参考
├── pydantic_schema_design.md       # ⭐ v0.1: Pydantic schema 设计规范
├── feishu_card_components.md       # 飞书卡片组件参考
├── morning_standup_format.md       # 早会总结格式规范
└── examples/
    ├── case_normal_day.md          # 正常日报样例
    ├── case_sla_breach_day.md      # SLA 临近日报样例
    └── case_high_volume_day.md     # 高量日报样例
```

---

## 错误地图

| 异常 | 触发 | 处理 | 用户看到 |
|---|---|---|---|
| `LangBotPluginError` | LangBot 加载失败 | 检查 plugin 路径 | "HLZD 日报助手插件加载失败" |
| `EventCollectError` | 数据源拉取失败 | 部分数据 + 提示 | "⚠️ 邮件数据拉取失败，日报基于 IM/订单" |
| `LLMOutputError` | Pydantic 验证失败 | 自动重试 1 次 + fallback | "AI 生成日报失败，请人工填写" |
| `FeishuSendError` | 飞书卡片发送失败 | 重试 + 邮件备份 | "飞书发送失败，已备份到邮件" |
| `MissingDataError` | 某数据源完全不可用 | 标注数据缺失 | "📊 今日订单数据缺失（API 异常）" |

---

## 自动串联规则

```markdown
## 自动串联

### 上游
- Panmira scheduler: 每日 18:00 触发
- LangBot 飞书适配器: 飞书消息触发（"今日日报"）
- HLZD-日报助手 插件注册到 LangBot

### 下游（4 大数据源拉取）
- HLZD-询盘响应 skill: imap_tools 拉今日邮件
- 飞书 API: 拉今日 IM 对话（LangBot 飞书适配器）
- HLZD-智能报价 skill: SQLite 查今日报价
- HLZD-物流装箱 skill: SQLite 查今日装箱
- HLZD-客户画像 skill: SQLite 查今日客户互动

### 平行（次日 8:00）
- 早会总结: 从昨日日报生成 to do list 完成度

### 协同
- 飞书卡片按钮 → 一键提交主管 Dashboard
- 飞书多维表格: 日报数据写入（主管 dashboard）
- HLZD-询盘响应 skill SLA 检测: 提供风险提醒数据
```

---

## 验证清单

- [ ] LangBot 飞书适配器加载成功
- [ ] HLZD 日报助手作为 LangBot 插件注册
- [ ] 每日 18:00 自动触发（Panmira scheduler）
- [ ] 4 大数据源聚合（邮件/IM/订单/客户）
- [ ] Event heartbeat 合并（ActivityWatch）
- [ ] LLM 生成日报（Claude + Pydantic 验证）
- [ ] 飞书卡片渲染（card-renderer）
- [ ] 一键提交主管 Dashboard
- [ ] 早会总结生成（次日 8:00）
- [ ] 风险提醒（SLA/投诉/危险品）

---

## 性能目标

| 路径 | 目标 | 预估 |
|---|---|---|
| 4 大数据源聚合 | < 10s | 5-8s（并行）|
| Event heartbeat 合并 | < 1s | 0.3s |
| LLM 生成日报 | < 30s | 15-25s |
| 飞书卡片渲染 | < 2s | 0.5s |
| 飞书卡片推送 | < 3s | 1-2s |
| 早会总结生成 | < 15s | 5-10s |
| **总耗时** | **< 60s** | **30-50s** |

---

## 安全考虑

1. **日报数据隔离**——每个业务员只看自己的日报
2. **跨租户隔离**——不同 HLZD 子公司数据不混淆
3. **LLM context 安全**——日报数据脱敏（不展示客户敏感信息）
4. **审计日志**——日报提交记录保存 5 年
5. **飞书多维表格权限**——主管只看团队日报，不看个人隐私

---

## 已知限制（v0.1 接受）

1. **不接 LangBot 实时部署**——v0.1 仅设计插件接口，部署由 LangBot 框架负责
2. **不接外部 CRM 自动同步**——日报数据基于 HLZD 内部 SQLite
3. **不做日报模板自定义**——日报结构固定（v0.2 升级）
4. **不做日报 AI 评分**——日报准确性靠业务员自查（v0.2）
5. **不接语音日报**——只支持文本（v0.2）

---

## 后续路线

| 版本 | 新增 |
|---|---|
| v0.1 | ✅ LangBot 插件 + ActivityWatch 数据模型 + Inbox Zero Pydantic |
| **v0.2** | 日报模板自定义 + AI 评分 + 语音日报 |
| **v0.2** | 周报/月报聚合（日报自动汇总）|
| **v0.3** | 主管 dashboard 实时更新（飞书多维表格）|
| **v0.3** | 日报异常自动告警（日报漏提交/数据异常）|
| v0.4 | 业务员目标 vs 实际对比（KPI 自动追踪）|

---

## 文件位置

```
目标位置: ~/.claude/skills/hlzd-daily-report/
SKILL.md: ~/.claude/skills/hlzd-daily-report/SKILL.md
presets/: ~/.claude/skills/hlzd-daily-report/presets/
references/: ~/.claude/skills/hlzd-daily-report/references/
scripts/: ~/.claude/skills/hlzd-daily-report/scripts/
```

---

**END of HLZD-日报助手 v0.1 SKILL.md**

**关键借鉴 3 个开源项目**：
- 🏆 **langbot-app/LangBot**（16,712 stars）—— HLZD 日报助手作为 LangBot 插件（**不自己写飞书机器人**）
- 🏆 **ActivityWatch/activitywatch**（18,136 stars）—— Event/Bucket 数据模型 + heartbeat 合并
- 🏆 **Inbox Zero**（11,550 stars）—— Pydantic 结构化输出验证