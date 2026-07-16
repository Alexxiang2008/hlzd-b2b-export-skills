"""
海联智达-数据底座版 PPT v3.5-DataHub
基于 v3.5 商务版，聚焦：
- 数据底座（核心）
- 2 个 AI 技能：自动报价 + 基础客户回复
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ========== 设计常量 ==========
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# 数据底座版配色：科技蓝 + 渐变紫 + 数据绿
NAVY = RGBColor(0x0A, 0x1F, 0x44)
PRIMARY = RGBColor(0x1F, 0x6F, 0xEB)
PURPLE = RGBColor(0x6D, 0x28, 0xD9)        # 紫（AI 技能）
ACCENT = RGBColor(0x10, 0xB9, 0x81)        # 绿（增长/数据）
GOLD = RGBColor(0xC9, 0xA2, 0x27)          # 金（高亮）
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF8, 0xFA, 0xFC)
GRAY = RGBColor(0x6B, 0x72, 0x80)
DARK = RGBColor(0x1E, 0x29, 0x37)

FONT = "Microsoft YaHei"


# ========== 工具函数 ==========
def set_text(tf, text, size=18, bold=False, color=DARK, align=PP_ALIGN.LEFT, font=FONT):
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    rPr = run._r.get_or_add_rPr()
    eastAsia = etree.SubElement(rPr, qn('a:ea'))
    eastAsia.set('typeface', font)


def add_text(slide, x, y, w, h, text, size=18, bold=False, color=DARK, align=PP_ALIGN.LEFT, font=FONT):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    set_text(tf, text, size, bold, color, align, font)
    return tb


def add_rect(slide, x, y, w, h, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.5)
    s.shadow.inherit = False
    return s


def add_rounded(slide, x, y, w, h, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    s.shadow.inherit = False
    return s


def set_bg(slide, color=WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_biz_header(slide, page_num, total, section):
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), PRIMARY)
    add_text(slide, Inches(0.4), Inches(0.18), Inches(3), Inches(0.3),
             "海联智达", size=11, bold=True, color=PRIMARY)
    add_text(slide, Inches(0.4), Inches(0.5), Inches(8), Inches(0.3),
             section, size=10, color=GRAY)
    add_text(slide, Inches(12.2), Inches(0.18), Inches(1), Inches(0.3),
             f"{page_num:02d} / {total:02d}", size=10, color=GRAY, align=PP_ALIGN.RIGHT)
    add_rect(slide, Inches(0.4), Inches(0.85), Inches(12.5), Inches(0.02), PURPLE)


def add_page_title(slide, title, subtitle=None):
    add_text(slide, Inches(0.4), Inches(1.1), Inches(12.5), Inches(0.6),
             title, size=28, bold=True, color=NAVY)
    if subtitle:
        add_text(slide, Inches(0.4), Inches(1.75), Inches(12.5), Inches(0.4),
                 subtitle, size=12, color=GRAY)


# ========== 10 张幻灯片 ==========
def make_cover(slide, page_num, total):
    """封面"""
    set_bg(slide, NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.12), GOLD)

    add_text(slide, Inches(0.6), Inches(0.6), Inches(4), Inches(0.4),
             "BUSINESS PRESENTATION  |  商务版", size=10, color=GOLD, bold=True)
    add_rect(slide, Inches(0.6), Inches(1.1), Inches(2), Inches(0.04), GOLD)

    add_text(slide, Inches(0.6), Inches(1.5), Inches(12), Inches(1.2),
             "海联智达 × 智能数据底座", size=46, bold=True, color=WHITE)
    add_text(slide, Inches(0.6), Inches(2.6), Inches(12), Inches(1.0),
             "Data Hub + AI Skills", size=24, color=GOLD)

    add_text(slide, Inches(0.6), Inches(3.9), Inches(12), Inches(0.6),
             "一个数据底座 + 两个 AI 技能 = 自动报价 + 客户回复", size=18, color=WHITE)

    # 三大卖点
    add_rounded(slide, Inches(0.6), Inches(5.0), Inches(4.0), Inches(1.5), PRIMARY)
    add_text(slide, Inches(0.6), Inches(5.1), Inches(4.0), Inches(0.4),
             "数据底座", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.6), Inches(5.5), Inches(4.0), Inches(0.9),
             "打通 ERP / CRM / 邮件 / 文档\n构建外贸企业专属数据资产", size=11,
             color=WHITE, align=PP_ALIGN.CENTER)

    add_rounded(slide, Inches(4.7), Inches(5.0), Inches(4.0), Inches(1.5), PURPLE)
    add_text(slide, Inches(4.7), Inches(5.1), Inches(4.0), Inches(0.4),
             "AI 技能 · 自动报价", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(4.7), Inches(5.5), Inches(4.0), Inches(0.9),
             "询盘 → 报价单 自动生成\n30 秒响应，无需人工录入", size=11,
             color=WHITE, align=PP_ALIGN.CENTER)

    add_rounded(slide, Inches(8.8), Inches(5.0), Inches(4.0), Inches(1.5), ACCENT)
    add_text(slide, Inches(8.8), Inches(5.1), Inches(4.0), Inches(0.4),
             "AI 技能 · 客户回复", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(8.8), Inches(5.5), Inches(4.0), Inches(0.9),
             "7×24 自动回复邮件 / WhatsApp\n保留人工升级通道", size=11,
             color=WHITE, align=PP_ALIGN.CENTER)

    add_text(slide, Inches(0.6), Inches(6.8), Inches(12), Inches(0.3),
             "v3.5-DataHub  |  2026.07", size=10, color=GOLD_LIGHT if False else GRAY)


def make_pain(slide, page_num, total):
    """痛点"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "01  MARKET PAIN  ·  痛点共鸣")
    add_page_title(slide, "外贸企业的数据困局", "数据散落在 5+ 系统，AI 落地无根基")

    # 5 个痛点
    pains = [
        ("数据散落", "ERP / CRM / 邮件\n表格 / 文档 / IM", PRIMARY),
        ("重复录入", "80% 询盘信息\n需人工手动复制", PURPLE),
        ("响应延迟", "报价平均 4.8 小时\n客户已流失", ACCENT),
        ("客服瓶颈", "夜间询盘无人响应\n转化率打 5 折", GOLD),
        ("无法沉淀", "员工离职带走经验\n企业数据归零", GRAY),
    ]
    pw = Inches(2.4)
    pg = Inches(0.15)
    px = Inches(0.4)
    py = Inches(2.5)
    for i, (title, desc, color) in enumerate(pains):
        x = px + (pw + pg) * i
        add_rounded(slide, x, py, pw, Inches(2.8), LIGHT)
        add_rect(slide, x, py, pw, Inches(0.5), color)
        add_text(slide, x, py + Inches(0.05), pw, Inches(0.4),
                 f"0{i+1}", size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.1), py + Inches(0.7), pw - Inches(0.2), Inches(0.5),
                 title, size=15, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.1), py + Inches(1.3), pw - Inches(0.2), Inches(1.3),
                 desc, size=12, color=DARK, align=PP_ALIGN.CENTER)

    # 核心洞察
    add_rounded(slide, Inches(0.4), Inches(5.6), Inches(12.5), Inches(1.2), NAVY)
    add_text(slide, Inches(0.4), Inches(5.7), Inches(12.5), Inches(0.4),
             "💡 核心洞察", size=14, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(6.1), Inches(12.5), Inches(0.6),
             "AI 落地的最大障碍不是模型，而是「没有干净、结构化、可被 AI 读取的数据」", size=16,
             color=WHITE, align=PP_ALIGN.CENTER, bold=True)


def make_solution(slide, page_num, total):
    """解决方案"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "02  SOLUTION  ·  解决方案")
    add_page_title(slide, "1 个数据底座 + 2 个 AI 技能", "先把数据打通，再让 AI 有用武之地")

    # 左侧：数据底座
    add_rounded(slide, Inches(0.4), Inches(2.4), Inches(6.0), Inches(4.5), WHITE, line=PRIMARY)
    add_rect(slide, Inches(0.4), Inches(2.4), Inches(6.0), Inches(0.6), PRIMARY)
    add_text(slide, Inches(0.4), Inches(2.5), Inches(6.0), Inches(0.4),
             "🏛️  数据底座（核心）", size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    base_layers = [
        ("L1 数据采集", "ERP / CRM / 邮件 / 文档 / IM"),
        ("L2 数据清洗", "标准化、去重、关联、补全"),
        ("L3 数据建模", "产品 / 客户 / 价格 / 询盘 4 大实体"),
        ("L4 数据接口", "API + MCP 协议，AI 技能直接调用"),
    ]
    ly = Inches(3.15)
    for label, desc in base_layers:
        add_rounded(slide, Inches(0.7), ly, Inches(5.4), Inches(0.78), LIGHT)
        add_text(slide, Inches(0.85), ly + Inches(0.05), Inches(1.5), Inches(0.4),
                 label, size=12, bold=True, color=PRIMARY)
        add_text(slide, Inches(0.85), ly + Inches(0.4), Inches(5.0), Inches(0.4),
                 desc, size=11, color=DARK)
        ly += Inches(0.88)

    # 右侧：2 个 AI 技能
    add_rounded(slide, Inches(6.7), Inches(2.4), Inches(6.2), Inches(2.15), WHITE, line=PURPLE)
    add_rect(slide, Inches(6.7), Inches(2.4), Inches(6.2), Inches(0.5), PURPLE)
    add_text(slide, Inches(6.7), Inches(2.5), Inches(6.2), Inches(0.3),
             "🤖  AI 技能 1：自动报价引擎", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(7.0), Inches(3.05), Inches(5.6), Inches(0.4),
             "输入：客户询盘邮件/表单", size=11, color=GRAY)
    add_text(slide, Inches(7.0), Inches(3.4), Inches(5.6), Inches(0.4),
             "  ↓ 匹配数据底座 ↓", size=11, color=PRIMARY, bold=True)
    add_text(slide, Inches(7.0), Inches(3.75), Inches(5.6), Inches(0.4),
             "输出：PDF 报价单（含产品规格/价格/交期）", size=11, color=GRAY)
    add_text(slide, Inches(7.0), Inches(4.1), Inches(5.6), Inches(0.4),
             "⏱ 响应时间：< 30 秒", size=12, color=PURPLE, bold=True)

    add_rounded(slide, Inches(6.7), Inches(4.7), Inches(6.2), Inches(2.2), WHITE, line=ACCENT)
    add_rect(slide, Inches(6.7), Inches(4.7), Inches(6.2), Inches(0.5), ACCENT)
    add_text(slide, Inches(6.7), Inches(4.8), Inches(6.2), Inches(0.3),
             "💬  AI 技能 2：基础客户回复", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(7.0), Inches(5.35), Inches(5.6), Inches(0.4),
             "支持渠道：邮件 / WhatsApp / 网页表单", size=11, color=GRAY)
    add_text(slide, Inches(7.0), Inches(5.7), Inches(5.6), Inches(0.4),
             "自动处理：FAQ / 产品咨询 / 询价引导", size=11, color=GRAY)
    add_text(slide, Inches(7.0), Inches(6.05), Inches(5.6), Inches(0.4),
             "人工升级：复杂问题自动转人工", size=11, color=GRAY)
    add_text(slide, Inches(7.0), Inches(6.4), Inches(5.6), Inches(0.4),
             "⏱ 7×24 在线 · 多语言", size=12, color=ACCENT, bold=True)


def make_architecture(slide, page_num, total):
    """数据底座架构"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "03  DATA HUB  ·  数据底座架构")
    add_page_title(slide, "数据底座 · 4 层架构", "打通外贸企业的全部数据源，构建 AI-ready 资产")

    # 4 层架构（横向）
    layers = [
        ("L1  数据采集", "5+ 数据源自动接入", PRIMARY,
         ["ERP（金蝶/用友/SAP）", "CRM（Salesforce/HubSpot）", "邮件（Exchange/IMAP）",
          "文档（PDF/Word/Excel）", "即时通讯（WhatsApp/微信）", "表格（Google Sheets）"]),
        ("L2  数据清洗", "AI 驱动的 ETL 流水线", ACCENT,
         ["去重 · 关联 · 补全", "格式标准化", "异常值检测", "自动归档", "版本控制", "审计日志"]),
        ("L3  数据建模", "4 大业务实体", PURPLE,
         ["产品库（规格/价格/库存）", "客户库（公司/联系人/历史）",
          "询盘库（需求/状态/转化）", "报价库（模板/审批/历史）",
          "供应商库", "合规规则库"]),
        ("L4  数据接口", "MCP 协议 + 标准 API", GOLD,
         ["REST API", "GraphQL", "MCP 协议", "Webhook",
          "文件导入/导出", "BI 工具集成"]),
    ]
    lw = Inches(3.0)
    lg = Inches(0.15)
    lx = Inches(0.4)
    ly = Inches(2.4)
    for i, (title, sub, color, items) in enumerate(layers):
        x = lx + (lw + lg) * i
        add_rounded(slide, x, ly, lw, Inches(4.5), WHITE, line=color)
        add_rect(slide, x, ly, lw, Inches(0.7), color)
        add_text(slide, x, ly + Inches(0.05), lw, Inches(0.35),
                 title, size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x, ly + Inches(0.38), lw, Inches(0.3),
                 sub, size=10, color=WHITE, align=PP_ALIGN.CENTER)
        item_y = ly + Inches(0.85)
        for item in items:
            add_text(slide, x + Inches(0.2), item_y, lw - Inches(0.3), Inches(0.35),
                     f"• {item}", size=11, color=DARK)
            item_y += Inches(0.36)

    # 底部说明
    add_rounded(slide, Inches(0.4), Inches(7.0), Inches(12.5), Inches(0.4), LIGHT)
    add_text(slide, Inches(0.4), Inches(7.05), Inches(12.5), Inches(0.3),
             "🔒 数据本地化部署 · TLS 1.3 + AES-256 加密 · 符合 GDPR / 中国《数据安全法》",
             size=11, color=DARK, align=PP_ALIGN.CENTER)


def make_skill_quote(slide, page_num, total):
    """AI 技能 1：自动报价"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "04  AI SKILL · 自动报价")
    add_page_title(slide, "AI 技能 1：自动报价引擎",
                   "客户询盘 → 30 秒生成 PDF 报价单 · 节省 80% 报价时间")

    # 流程图（5 步）
    flow = [
        ("①", "询盘接入", "邮件/表单\n自动抓取", PRIMARY),
        ("②", "需求解析", "AI 提取\n产品/数量/规格", PURPLE),
        ("③", "数据查询", "调用数据底座\n价格/库存/交期", ACCENT),
        ("④", "报价生成", "AI 拼装\nPDF 报价单", GOLD),
        ("⑤", "审批发送", "人工快速复核\n一键发送", GRAY),
    ]
    fw = Inches(2.4)
    fg = Inches(0.1)
    fx = Inches(0.4)
    fy = Inches(2.4)
    for i, (num, name, desc, color) in enumerate(flow):
        x = fx + (fw + fg) * i
        add_rounded(slide, x, fy, fw, Inches(2.0), WHITE, line=color)
        # 圆形编号
        add_rounded(slide, x + Inches(0.95), fy + Inches(0.1), Inches(0.5), Inches(0.5), color)
        add_text(slide, x + Inches(0.95), fy + Inches(0.13), Inches(0.5), Inches(0.4),
                 num, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x, fy + Inches(0.7), fw, Inches(0.4),
                 name, size=15, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.1), fy + Inches(1.15), fw - Inches(0.2), Inches(0.8),
                 desc, size=11, color=DARK, align=PP_ALIGN.CENTER)
        # 箭头
        if i < 4:
            add_text(slide, x + fw + Inches(0.01), fy + Inches(0.85), Inches(0.15), Inches(0.3),
                     "▶", size=18, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER)

    # 底部：效果指标
    add_text(slide, Inches(0.4), Inches(4.7), Inches(12.5), Inches(0.4),
             "📊 效果指标", size=16, bold=True, color=NAVY)
    metrics = [
        ("30s", "平均报价生成时间", PRIMARY),
        ("80%", "人工报价时间节省", PURPLE),
        ("95%", "报价准确率（基于数据底座）", ACCENT),
        ("3x", "询盘转化率提升", GOLD),
    ]
    mw = Inches(3.0)
    mg = Inches(0.15)
    mx = Inches(0.4)
    my = Inches(5.2)
    for i, (val, label, color) in enumerate(metrics):
        x = mx + (mw + mg) * i
        add_rounded(slide, x, my, mw, Inches(1.6), WHITE, line=color)
        add_text(slide, x, my + Inches(0.15), mw, Inches(0.7),
                 val, size=36, bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(slide, x, my + Inches(0.9), mw, Inches(0.6),
                 label, size=12, color=DARK, align=PP_ALIGN.CENTER)


def make_skill_chat(slide, page_num, total):
    """AI 技能 2：客户回复"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "05  AI SKILL · 客户回复")
    add_page_title(slide, "AI 技能 2：基础客户回复",
                   "7×24 在线 · 多语言 · 智能升级人工")

    # 左侧：能力矩阵
    add_rounded(slide, Inches(0.4), Inches(2.4), Inches(6.2), Inches(4.6), WHITE, line=ACCENT)
    add_rect(slide, Inches(0.4), Inches(2.4), Inches(6.2), Inches(0.6), ACCENT)
    add_text(slide, Inches(0.4), Inches(2.5), Inches(6.2), Inches(0.4),
             "✅ 自动处理场景", size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    scenarios = [
        ("FAQ 常见问题", "发货时间 / 付款方式 / 物流方式"),
        ("产品咨询", "规格 / 颜色 / 材质 / 认证"),
        ("询价引导", "收集数量 / 目的国 / 用途"),
        ("物流追踪", "订单号查询 / 物流公司"),
        ("多语言支持", "中 / 英 / 西 / 阿 / 法 5 国语言"),
    ]
    sy = Inches(3.15)
    for title, desc in scenarios:
        add_rounded(slide, Inches(0.7), sy, Inches(5.6), Inches(0.65), LIGHT)
        add_text(slide, Inches(0.85), sy + Inches(0.05), Inches(2), Inches(0.55),
                 f"✓ {title}", size=12, bold=True, color=ACCENT)
        add_text(slide, Inches(2.85), sy + Inches(0.05), Inches(3.5), Inches(0.55),
                 desc, size=11, color=DARK)
        sy += Inches(0.72)

    # 右侧：智能升级
    add_rounded(slide, Inches(6.9), Inches(2.4), Inches(6.0), Inches(4.6), WHITE, line=PURPLE)
    add_rect(slide, Inches(6.9), Inches(2.4), Inches(6.0), Inches(0.6), PURPLE)
    add_text(slide, Inches(6.9), Inches(2.5), Inches(6.0), Inches(0.4),
             "🤝 智能升级人工", size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    upgrade_flow = [
        ("意图识别", "AI 判断\n是否需人工", PURPLE),
        ("上下文打包", "完整对话\n+ 客户档案", PRIMARY),
        ("通知人工", "微信 / 钉钉\n推送提醒", ACCENT),
        ("无缝接管", "人工无需\n重复问背景", GOLD),
    ]
    uy = Inches(3.3)
    for i, (title, desc, color) in enumerate(upgrade_flow):
        col = i % 2
        row = i // 2
        ux = Inches(7.1 + col * 2.85)
        uy_pos = uy + row * Inches(0.95)
        add_rounded(slide, ux, uy_pos, Inches(2.7), Inches(0.85), LIGHT)
        add_rect(slide, ux, uy_pos, Inches(0.1), Inches(0.85), color)
        add_text(slide, ux + Inches(0.2), uy_pos + Inches(0.05), Inches(2.5), Inches(0.4),
                 title, size=12, bold=True, color=NAVY)
        add_text(slide, ux + Inches(0.2), uy_pos + Inches(0.42), Inches(2.5), Inches(0.4),
                 desc, size=10, color=DARK)

    # 底部
    add_text(slide, Inches(6.9), Inches(5.4), Inches(6.0), Inches(0.4),
             "确保 AI 处理 80%，复杂问题精准升级", size=12, bold=True, color=PURPLE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(6.9), Inches(5.85), Inches(6.0), Inches(0.8),
             "避免 100% AI 答非所问的负面体验，\n也避免 100% 人工的延迟与重复劳动", size=11,
             color=DARK, align=PP_ALIGN.CENTER)


def make_business(slide, page_num, total):
    """商务合作"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "06  COOPERATION  ·  商务合作")
    add_page_title(slide, "3 档套餐 · 按数据量选择",
                   "选最低档也能完整使用 数据底座 + 2 个 AI 技能")

    packages = [
        ("入门版", "STANDARD", "¥59,800", "数据量 ≤ 5 万条", PRIMARY,
         ["数据底座（4 层全功能）", "AI 技能：自动报价", "AI 技能：基础客户回复",
          "1 个租户 / 5 个用户", "30 天搭建 / 60 天首批询盘", "7×24 工程师支持"]),
        ("专业版", "PROFESSIONAL", "¥99,800", "数据量 ≤ 50 万条", ACCENT,
         ["入门版全部配置", "+ 多租户管理", "+ 自定义 AI 技能", "+ 数据看板",
          "+ 跨境合规规则库", "+ 季度业务复盘"]),
        ("企业版", "ENTERPRISE", "¥188,000", "数据量不限", PURPLE,
         ["专业版全部配置", "+ 私有化部署", "+ 定制 AI 技能", "+ 工程师上门",
          "+ SLA 99.9%", "+ 年度战略对齐"]),
    ]
    pw = Inches(4.0)
    pg = Inches(0.2)
    px = Inches(0.4)
    py = Inches(2.4)
    for i, (name, eng, price, target, color, features) in enumerate(packages):
        x = px + (pw + pg) * i
        add_rounded(slide, x, py, pw, Inches(4.5), WHITE, line=color)
        add_rect(slide, x, py, pw, Inches(0.7), color)
        add_text(slide, x, py + Inches(0.05), pw, Inches(0.3),
                 name, size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x, py + Inches(0.4), pw, Inches(0.3),
                 eng, size=9, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x, py + Inches(0.85), pw, Inches(0.6),
                 price, size=24, bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(slide, x, py + Inches(1.5), pw, Inches(0.3),
                 target, size=11, color=GRAY, align=PP_ALIGN.CENTER)
        fy = py + Inches(1.95)
        for f in features:
            add_text(slide, x + Inches(0.2), fy, pw - Inches(0.3), Inches(0.4),
                     f"✓ {f}", size=10, color=DARK)
            fy += Inches(0.4)


def make_commitment(slide, page_num, total):
    """商务保障"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "07  COMMITMENT  ·  商务保障")
    add_page_title(slide, "30/60 承诺 + 数据安全 + 7×24 服务",
                   "效果写进合同，不达标准免费延期")

    # 30/60 大字
    add_rounded(slide, Inches(0.4), Inches(2.4), Inches(6.0), Inches(2.5), PRIMARY)
    add_text(slide, Inches(0.4), Inches(2.6), Inches(6.0), Inches(1.0),
             "30", size=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(3.6), Inches(6.0), Inches(0.4),
             "天系统搭建", size=18, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(4.0), Inches(6.0), Inches(0.5),
             "DATA HUB READY", size=10, color=GOLD, align=PP_ALIGN.CENTER, bold=True)

    add_rounded(slide, Inches(6.9), Inches(2.4), Inches(6.0), Inches(2.5), ACCENT)
    add_text(slide, Inches(6.9), Inches(2.6), Inches(6.0), Inches(1.0),
             "60", size=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(6.9), Inches(3.6), Inches(6.0), Inches(0.4),
             "天首批询盘", size=18, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(6.9), Inches(4.0), Inches(6.0), Inches(0.5),
             "AI SKILLS LIVE", size=10, color=GOLD, align=PP_ALIGN.CENTER, bold=True)

    # 三大保障
    guarantees = [
        ("数据安全", "本地化部署 + 加密\n符合 GDPR / 中国法规"),
        ("7×24 工程师", "专属服务群\n1 小时首次响应"),
        ("效果写进合同", "30/60 不达标\n免费延期至达标"),
    ]
    gw = Inches(4.0)
    gg = Inches(0.15)
    gx = Inches(0.4)
    gy = Inches(5.2)
    for i, (title, desc) in enumerate(guarantees):
        x = gx + (gw + gg) * i
        add_rounded(slide, x, gy, gw, Inches(1.5), LIGHT)
        add_text(slide, x + Inches(0.2), gy + Inches(0.1), gw - Inches(0.4), Inches(0.4),
                 title, size=15, bold=True, color=PRIMARY)
        add_text(slide, x + Inches(0.2), gy + Inches(0.55), gw - Inches(0.4), Inches(0.8),
                 desc, size=11, color=DARK)


def make_team(slide, page_num, total):
    """团队（数据底座 + AI 背景）"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "08  OUR TEAM  ·  核心团队")
    add_page_title(slide, "数据底座 + AI 双重背景", "既懂数据架构，又懂 AI 工程化")

    members = [
        ("创始团队", "出海老兵", "10+ 年外贸业务经验\n理解工厂真实数据痛点"),
        ("技术团队", "数据架构师", "前阿里 / 字节数据中台\n主导过 PB 级数据治理"),
        ("AI 团队", "AI 工程师", "RAG / Agent 工程化\n让 AI 真正读懂业务数据"),
    ]
    mw = Inches(3.9)
    mg = Inches(0.15)
    mx = Inches(0.4)
    my = Inches(2.4)
    for i, (cat, role, desc) in enumerate(members):
        x = mx + (mw + mg) * i
        add_rounded(slide, x, my, mw, Inches(2.4), LIGHT)
        add_rect(slide, x, my, Inches(0.12), Inches(2.4), PRIMARY)
        add_text(slide, x + Inches(0.3), my + Inches(0.15), mw - Inches(0.4), Inches(0.4),
                 cat, size=12, color=GRAY)
        add_text(slide, x + Inches(0.3), my + Inches(0.55), mw - Inches(0.4), Inches(0.5),
                 role, size=20, bold=True, color=PRIMARY)
        add_text(slide, x + Inches(0.3), my + Inches(1.15), mw - Inches(0.4), Inches(1.0),
                 desc, size=12, color=DARK)

    # 我们的使命
    add_rounded(slide, Inches(0.4), Inches(5.1), Inches(12.5), Inches(1.7), NAVY)
    add_text(slide, Inches(0.4), Inches(5.2), Inches(12.5), Inches(0.4),
             "OUR MISSION  ·  我们的使命", size=11, color=GOLD, align=PP_ALIGN.CENTER, bold=True)
    add_text(slide, Inches(0.4), Inches(5.6), Inches(12.5), Inches(0.8),
             "让 AI 从「工具」变「员工的队友」", size=24, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(6.4), Inches(12.5), Inches(0.4),
             "从数据底座开始，让 AI 真正赋能每一个外贸员工", size=12, color=GOLD_LIGHT if False else GOLD, align=PP_ALIGN.CENTER)


def make_contact(slide, page_num, total):
    """合作邀请（CTA）"""
    set_bg(slide, NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.12), GOLD)
    add_text(slide, Inches(0.6), Inches(0.6), Inches(4), Inches(0.4),
             "BUSINESS COOPERATION  |  开启合作", size=10, color=GOLD, bold=True)
    add_rect(slide, Inches(0.6), Inches(1.1), Inches(2), Inches(0.04), GOLD)

    add_text(slide, Inches(0.6), Inches(1.5), Inches(12), Inches(1.0),
             "从数据底座开始", size=54, bold=True, color=WHITE)
    add_text(slide, Inches(0.6), Inches(2.6), Inches(12), Inches(0.8),
             "30 天搭建 · 60 天首批询盘", size=28, bold=True, color=GOLD)

    add_text(slide, Inches(0.6), Inches(3.7), Inches(12), Inches(0.5),
             "海联智达 × 智能数据底座 + AI 技能", size=16, color=WHITE)

    # 3 种合作路径
    add_text(slide, Inches(0.6), Inches(4.6), Inches(12), Inches(0.4),
             "3 种合作路径", size=14, color=GOLD)
    paths = [
        ("① 直接采购", "选入门版 ¥59,800 起步\n签约即启动 30/60"),
        ("② 战略合作", "联合行业头部工厂\n共建国贸数据联盟"),
        ("③ 渠道代理", "区域市场代理\n享受高额返点"),
    ]
    path_colors = [PRIMARY, ACCENT, PURPLE]
    pw = Inches(3.9)
    pg = Inches(0.15)
    px = Inches(0.6)
    py = Inches(5.05)
    for i, (title, desc) in enumerate(paths):
        x = px + (pw + pg) * i
        add_rounded(slide, x, py, pw, Inches(1.4), NAVY, line=GOLD)
        add_text(slide, x + Inches(0.2), py + Inches(0.1), pw - Inches(0.4), Inches(0.4),
                 title, size=15, bold=True, color=GOLD)
        add_text(slide, x + Inches(0.2), py + Inches(0.55), pw - Inches(0.4), Inches(0.7),
                 desc, size=11, color=WHITE)

    add_text(slide, Inches(0.6), Inches(6.7), Inches(12), Inches(0.4),
             "📧 business@hailian-zhida.com  |  📞  186-5463-9599", size=14,
             color=WHITE, align=PP_ALIGN.LEFT, bold=True)
    add_text(slide, Inches(0.6), Inches(7.0), Inches(12), Inches(0.3),
             "期待与您共建数据驱动的国贸新生态", size=11, color=GOLD, align=PP_ALIGN.LEFT)


# ========== 主流程 ==========
def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    total = 10
    builders = [
        make_cover,         # 1  封面
        make_pain,          # 2  痛点
        make_solution,      # 3  解决方案
        make_architecture,   # 4  数据底座架构
        make_skill_quote,    # 5  AI 技能 1：自动报价
        make_skill_chat,     # 6  AI 技能 2：客户回复
        make_business,       # 7  商务合作
        make_commitment,     # 8  商务保障
        make_team,           # 9  团队
        make_contact,        # 10 CTA
    ]
    for i, fn in enumerate(builders):
        slide = prs.slides.add_slide(blank)
        fn(slide, i + 1, total)
        print(f"  [OK] Slide {i+1}/{total} - {fn.__name__}")

    output = r'D:\MCP_SERVER\HLZD-SALES\海联智达-数据底座-v3.5-DataHub.pptx'
    prs.save(output)
    print(f"\n[OK] PPT: {output}")
    print(f"     Size: {os.path.getsize(output)/1024:.1f} KB")


if __name__ == "__main__":
    main()
