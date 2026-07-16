"""
海联智达 v3.6-DataHub-Enterprise
新核心：系统工程学方法论 + 从零到一 + 数据底座全维度
3 步核心动作：数据标准 → 数据清洗 → 数据整理
在底座之上：2 个 AI 技能（自动报价 + 客户回复）
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

# 新配色：系统工程 + 数据底座
NAVY = RGBColor(0x0A, 0x1F, 0x44)
PRIMARY = RGBColor(0x1F, 0x6F, 0xEB)
TEAL = RGBColor(0x06, 0xB6, 0xD4)          # 青（方法论）
PURPLE = RGBColor(0x6D, 0x28, 0xD9)        # 紫（AI 技能）
ACCENT = RGBColor(0x10, 0xB9, 0x81)        # 绿（增长）
GOLD = RGBColor(0xC9, 0xA2, 0x27)
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
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), TEAL)
    add_text(slide, Inches(0.4), Inches(0.18), Inches(3), Inches(0.3),
             "海联智达", size=11, bold=True, color=PRIMARY)
    add_text(slide, Inches(0.4), Inches(0.5), Inches(10), Inches(0.3),
             section, size=10, color=GRAY)
    add_text(slide, Inches(12.2), Inches(0.18), Inches(1), Inches(0.3),
             f"{page_num:02d} / {total:02d}", size=10, color=GRAY, align=PP_ALIGN.RIGHT)
    add_rect(slide, Inches(0.4), Inches(0.85), Inches(12.5), Inches(0.02), TEAL)


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
    add_text(slide, Inches(0.6), Inches(0.6), Inches(6), Inches(0.4),
             "BUSINESS PRESENTATION  |  v3.6", size=10, color=GOLD, bold=True)
    add_rect(slide, Inches(0.6), Inches(1.1), Inches(2), Inches(0.04), GOLD)

    add_text(slide, Inches(0.6), Inches(1.5), Inches(12), Inches(1.0),
             "企业知识数字化方法论", size=48, bold=True, color=WHITE)
    add_text(slide, Inches(0.6), Inches(2.5), Inches(12), Inches(0.8),
             "从零到一搭建数据底座", size=32, bold=True, color=GOLD)
    add_text(slide, Inches(0.6), Inches(3.5), Inches(12), Inches(0.5),
             "Enterprise Knowledge Digitization Methodology", size=14, color=GOLD_LIGHT if False else GRAY)

    # 三大支柱
    add_rounded(slide, Inches(0.6), Inches(4.5), Inches(4.0), Inches(2.0), PRIMARY)
    add_text(slide, Inches(0.6), Inches(4.6), Inches(4.0), Inches(0.4),
             "🏛️ 全维度数据底座", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.6), Inches(5.05), Inches(4.0), Inches(1.4),
             "不是产品说明书\n是企业的全部知识资产\n产品/客户/流程/合规/邮件/历史经验", size=12,
             color=WHITE, align=PP_ALIGN.CENTER)

    add_rounded(slide, Inches(4.7), Inches(4.5), Inches(4.0), Inches(2.0), TEAL)
    add_text(slide, Inches(4.7), Inches(4.6), Inches(4.0), Inches(0.4),
             "🔬 系统工程学方法论", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(4.7), Inches(5.05), Inches(4.0), Inches(1.4),
             "3 步科学流程\n数据标准 → 数据清洗 → 数据整理\n每一步都有方法论支撑", size=12,
             color=WHITE, align=PP_ALIGN.CENTER)

    add_rounded(slide, Inches(8.8), Inches(4.5), Inches(4.0), Inches(2.0), PURPLE)
    add_text(slide, Inches(8.8), Inches(4.6), Inches(4.0), Inches(0.4),
             "🤖 2 个 AI 数字员工", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(8.8), Inches(5.05), Inches(4.0), Inches(1.4),
             "自动报价员 + 客户回复员\n针对企业情况定制\n7×24 释放业务员时间", size=12,
             color=WHITE, align=PP_ALIGN.CENTER)

    add_text(slide, Inches(0.6), Inches(6.85), Inches(12), Inches(0.4),
             "v3.6-DataHub-Enterprise  |  2026.07", size=10, color=GRAY, align=PP_ALIGN.CENTER)


def make_pain(slide, page_num, total):
    """痛点：企业的知识在沉睡"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "01  PROBLEM  ·  企业知识的沉默成本")
    add_page_title(slide, "80% 企业的知识在沉睡", "不是没有知识，是不知道如何整理")

    # 4 大沉默成本
    pains = [
        ("散落各处", "知识分散在 ERP/CRM/邮件/IM/表格/纸质文档\n无人知道全貌", PRIMARY),
        ("无从下手", "想做 AI 但不知道从哪开始\n缺乏科学方法论", TEAL),
        ("重复劳动", "新人入职从零学起\n老员工离职经验归零", PURPLE),
        ("试错浪费", "买过 SaaS / 招过 AI 工程师\n但效果不达预期", ACCENT),
    ]
    pw = Inches(6.0)
    pg = Inches(0.2)
    px = Inches(0.4)
    py = Inches(2.4)
    for i, (title, desc, color) in enumerate(pains):
        col = i % 2
        row = i // 2
        x = px + (pw + pg) * col
        y = py + Inches(2.0) * row
        add_rounded(slide, x, y, pw, Inches(1.8), WHITE, line=color)
        add_rect(slide, x, y, Inches(0.15), Inches(1.8), color)
        add_text(slide, x + Inches(0.3), y + Inches(0.15), pw - Inches(0.4), Inches(0.4),
                 f"❌ {title}", size=15, bold=True, color=color)
        add_text(slide, x + Inches(0.3), y + Inches(0.65), pw - Inches(0.4), Inches(1.0),
                 desc, size=12, color=DARK)

    # 核心洞察
    add_rounded(slide, Inches(0.4), Inches(6.5), Inches(12.5), Inches(0.8), NAVY)
    add_text(slide, Inches(0.4), Inches(6.55), Inches(12.5), Inches(0.3),
             "💡 核心洞察", size=12, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(6.85), Inches(12.5), Inches(0.4),
             "AI 落地的最大障碍不是技术，而是「企业不知道如何把自己的知识数字化」", size=14,
             bold=True, color=WHITE, align=PP_ALIGN.CENTER)


def make_redefine(slide, page_num, total):
    """重新定义：什么是数据底座"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "02  REDEFINE  ·  重新定义数据底座")
    add_page_title(slide, "数据底座 ≠ 产品知识库",
                   "数据底座 = 企业全维度知识资产")

    # ❌ vs ✅ 对比
    add_text(slide, Inches(0.4), Inches(2.4), Inches(6.0), Inches(0.4),
             "❌ 常见误解", size=18, bold=True, color=NAVY)
    add_text(slide, Inches(7.0), Inches(2.4), Inches(6.0), Inches(0.4),
             "✅ 海联智达定义", size=18, bold=True, color=ACCENT)

    myths = [
        ("数据底座 = 产品说明书", "数据底座 = 企业全部知识"),
        ("数据底座 = 客户信息表", "数据底座 = 客户/产品/流程/合规/经验的融合"),
        ("数据底座 = 知识问答", "数据底座 = 可被 AI 调用的结构化资产"),
        ("数据底座 = 数据库", "数据底座 = 含数据标准+清洗+整理的方法论体系"),
    ]
    my = Inches(2.95)
    for myth, truth in myths:
        # ❌ 左侧
        add_rounded(slide, Inches(0.4), my, Inches(6.0), Inches(0.6), LIGHT)
        add_rect(slide, Inches(0.4), my, Inches(0.12), Inches(0.6), RED := RGBColor(0xEF, 0x44, 0x44))
        add_text(slide, Inches(0.7), my + Inches(0.15), Inches(5.6), Inches(0.4),
                 "✕  " + myth, size=12, color=DARK)
        # ✅ 右侧
        add_rounded(slide, Inches(7.0), my, Inches(6.0), Inches(0.6), LIGHT)
        add_rect(slide, Inches(7.0), my, Inches(0.12), Inches(0.6), ACCENT)
        add_text(slide, Inches(7.3), my + Inches(0.15), Inches(5.6), Inches(0.4),
                 "✓  " + truth, size=12, color=DARK, bold=True)
        my += Inches(0.75)

    # 底部：数据底座的 8 大范畴
    add_rounded(slide, Inches(0.4), Inches(6.1), Inches(12.5), Inches(1.2), TEAL)
    add_text(slide, Inches(0.4), Inches(6.15), Inches(12.5), Inches(0.3),
             "📚 数据底座的 8 大知识范畴", size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    scopes = ["产品知识", "客户档案", "业务流程", "合规规则",
              "历史经验", "邮件往来", "合同条款", "内部文档"]
    sw = Inches(1.5)
    sg = Inches(0.05)
    sx = Inches(0.55)
    sy = Inches(6.55)
    for i, scope in enumerate(scopes):
        x = sx + (sw + sg) * i
        add_rounded(slide, x, sy, sw, Inches(0.6), WHITE)
        add_text(slide, x, sy, sw, Inches(0.6), scope, size=10, bold=True,
                 color=NAVY, align=PP_ALIGN.CENTER)


def make_methodology(slide, page_num, total):
    """系统工程学方法论 5 步"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "03  METHODOLOGY  ·  系统工程学 5 步法")
    add_page_title(slide, "海联智达方法论 · 5 步从零到一",
                   "用系统工程学的方法论，让企业知识数字化可复制、可交付")

    # 5 步流程
    steps = [
        ("① 业务建模", "梳理企业\n价值链 + 流程", PRIMARY, "2 周"),
        ("② 数据标准", "字段/命名/\n关联/元数据", TEAL, "2 周"),
        ("③ 数据采集", "5+ 系统\n自动接入", PURPLE, "2 周"),
        ("④ 数据清洗", "去重/纠错/\n补全/标准化", ACCENT, "2 周"),
        ("⑤ 数据整理", "结构化 +\nAI 化封装", GOLD, "2 周"),
    ]
    sw = Inches(2.4)
    sg = Inches(0.15)
    sx = Inches(0.4)
    sy = Inches(2.4)
    for i, (name, desc, color, time) in enumerate(steps):
        x = sx + (sw + sg) * i
        add_rounded(slide, x, sy, sw, Inches(3.0), WHITE, line=color)
        add_rect(slide, x, sy, sw, Inches(0.5), color)
        add_text(slide, x, sy + Inches(0.1), sw, Inches(0.4),
                 name, size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.2), sy + Inches(0.7), sw - Inches(0.4), Inches(1.0),
                 desc, size=12, color=DARK, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.2), sy + Inches(2.0), sw - Inches(0.4), Inches(0.4),
                 f"⏱ {time}", size=11, color=color, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.2), sy + Inches(2.4), sw - Inches(0.4), Inches(0.5),
                 "工程师上门\n驻场实施", size=10, color=GRAY, align=PP_ALIGN.CENTER)
        # 箭头
        if i < 4:
            add_text(slide, x + sw + Inches(0.01), sy + Inches(1.4), Inches(0.15), Inches(0.3),
                     "▶", size=20, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

    # 底部
    add_rounded(slide, Inches(0.4), Inches(5.7), Inches(12.5), Inches(1.5), NAVY)
    add_text(slide, Inches(0.4), Inches(5.8), Inches(12.5), Inches(0.4),
             "🎯 5 步法的核心差异", size=14, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(6.2), Inches(12.5), Inches(0.5),
             "不是「买个工具」，而是「一套针对企业定制的知识数字化工程」", size=16,
             color=WHITE, align=PP_ALIGN.CENTER, bold=True)
    add_text(slide, Inches(0.4), Inches(6.7), Inches(12.5), Inches(0.4),
             "工程师手把手陪跑，30 天交付可用的数据底座 + 2 个 AI 数字员工", size=12,
             color=GOLD, align=PP_ALIGN.CENTER)


def make_three_steps(slide, page_num, total):
    """3 步核心动作：标准/清洗/整理"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "04  THREE STEPS  ·  3 步核心动作")
    add_page_title(slide, "数据标准 / 清洗 / 整理",
                   "3 步决定数据底座质量 · 每步都有方法论 + 工具")

    steps = [
        ("① 数据标准", "Data Standard", "建立字段、命名、关联、元数据的统一规范", TEAL,
         ["字段标准：必填/选填/类型/格式", "命名规范：业务术语统一",
          "关联关系：实体之间逻辑定义", "元数据：来源/版本/责任人",
          "输出：《企业数据标准文档 v1.0》", "工具：DSL 标准定义语言"]),
        ("② 数据清洗", "Data Cleaning", "去重、纠错、补全、标准化", PURPLE,
         ["去重：实体级 / 字段级 / 跨表", "纠错：异常值 / 矛盾值 / 过期值",
          "补全：缺失字段智能推断", "标准化：格式/单位/币种",
          "输出：清洗报告 + 质量评分", "工具：自动化 ETL 流水线"]),
        ("③ 数据整理", "Data Structuring", "把清洗后的数据组织成可被 AI 调用的结构", ACCENT,
         ["实体建模：产品/客户/订单/...", "关联建模：实体间关系图",
          "索引优化：高频查询加速", "API 化：MCP 协议 + REST",
          "输出：可被 AI 直接调用的数据资产", "工具：知识图谱 + 向量库双引擎"]),
    ]
    sw = Inches(4.0)
    sg = Inches(0.2)
    sx = Inches(0.4)
    sy = Inches(2.4)
    for i, (num, eng, sub, color, items) in enumerate(steps):
        x = sx + (sw + sg) * i
        add_rounded(slide, x, sy, sw, Inches(4.7), WHITE, line=color)
        add_rect(slide, x, sy, sw, Inches(0.9), color)
        add_text(slide, x, sy + Inches(0.1), sw, Inches(0.4),
                 num, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x, sy + Inches(0.5), sw, Inches(0.3),
                 eng, size=10, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.2), sy + Inches(1.05), sw - Inches(0.4), Inches(0.6),
                 sub, size=12, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        # 6 项细节
        iy = sy + Inches(1.85)
        for item in items:
            add_text(slide, x + Inches(0.25), iy, sw - Inches(0.4), Inches(0.4),
                     "• " + item, size=10, color=DARK)
            iy += Inches(0.4)


def make_ai_skills(slide, page_num, total):
    """在底座之上的 2 个 AI 数字员工"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "05  AI EMPLOYEES  ·  2 个 AI 数字员工")
    add_page_title(slide, "底座建好之后 · 2 个 AI 数字员工上岗",
                   "针对企业情况定制 · 不需要再训练模型")

    # 流程图
    add_text(slide, Inches(0.4), Inches(2.4), Inches(12.5), Inches(0.4),
             "数据底座 + 2 个 AI 数字员工的协同关系", size=14, bold=True, color=NAVY)

    flow_steps = [
        ("数据底座", "产品/客户/流程/...\n已结构化资产", TEAL),
        ("AI 引擎", "RAG + Agent\nGPT/Claude 等", PURPLE),
        ("AI 数字员工 1", "🤖 自动报价员\n30 秒生成 PDF", PRIMARY),
        ("AI 数字员工 2", "💬 客户回复员\n7×24 多语言", ACCENT),
    ]
    fw = Inches(3.0)
    fg = Inches(0.1)
    fx = Inches(0.4)
    fy = Inches(2.95)
    for i, (name, desc, color) in enumerate(flow_steps):
        x = fx + (fw + fg) * i
        add_rounded(slide, x, fy, fw, Inches(1.4), WHITE, line=color)
        add_rect(slide, x, fy, fw, Inches(0.4), color)
        add_text(slide, x, fy + Inches(0.05), fw, Inches(0.3),
                 name, size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.15), fy + Inches(0.5), fw - Inches(0.3), Inches(0.8),
                 desc, size=11, color=DARK, align=PP_ALIGN.CENTER)
        if i < 3:
            add_text(slide, x + fw + Inches(0.01), fy + Inches(0.55), Inches(0.15), Inches(0.3),
                     "▶", size=18, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER)

    # 底部：员工详情
    add_rounded(slide, Inches(0.4), Inches(4.6), Inches(6.2), Inches(2.5), WHITE, line=PRIMARY)
    add_rect(slide, Inches(0.4), Inches(4.6), Inches(6.2), Inches(0.4), PRIMARY)
    add_text(slide, Inches(0.4), Inches(4.65), Inches(6.2), Inches(0.3),
             "🤖  AI 数字员工 1：自动报价员", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    quote_features = [
        "针对企业产品/价格/客户定制",
        "底座数据自动匹配（产品/价格/库存/交期）",
        "客户询盘 → 30 秒生成 PDF 报价单",
        "80% 节省人工报价时间",
    ]
    qy = Inches(5.15)
    for f in quote_features:
        add_text(slide, Inches(0.6), qy, Inches(5.8), Inches(0.4),
                 "✓ " + f, size=11, color=DARK)
        qy += Inches(0.4)

    add_rounded(slide, Inches(6.9), Inches(4.6), Inches(6.0), Inches(2.5), WHITE, line=ACCENT)
    add_rect(slide, Inches(6.9), Inches(4.6), Inches(6.0), Inches(0.4), ACCENT)
    add_text(slide, Inches(6.9), Inches(4.65), Inches(6.0), Inches(0.3),
             "💬  AI 数字员工 2：客户回复员", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    chat_features = [
        "针对企业常见问题定制",
        "邮件/WhatsApp/网页表单统一接入",
        "复杂问题智能升级人工 + 上下文打包",
        "7×24 在线 · 中英西阿法 5 国语言",
    ]
    qy = Inches(5.15)
    for f in chat_features:
        add_text(slide, Inches(7.1), qy, Inches(5.6), Inches(0.4),
                 "✓ " + f, size=11, color=DARK)
        qy += Inches(0.4)


def make_business(slide, page_num, total):
    """商务合作 - 单一价格 99800"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "06  COOPERATION  ·  商务合作")
    add_page_title(slide, "统一报价 ¥99,800 · 完整服务",
                   "针对企业情况定制 · 包含「方法论 + 5 步实施 + 数据底座 + 2 个 AI 数字员工」")

    # 左侧：价格卡片
    add_rounded(slide, Inches(0.4), Inches(2.4), Inches(5.5), Inches(4.7), NAVY)
    add_rect(slide, Inches(0.4), Inches(2.4), Inches(5.5), Inches(0.6), GOLD)
    add_text(slide, Inches(0.4), Inches(2.5), Inches(5.5), Inches(0.4),
             "🌟  完整服务包", size=15, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(3.3), Inches(5.5), Inches(0.5),
             "¥99,800", size=48, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(4.1), Inches(5.5), Inches(0.4),
             "首年服务费（含数据底座 + 2 个 AI 数字员工）", size=12,
             color=GOLD, align=PP_ALIGN.CENTER)

    add_text(slide, Inches(0.4), Inches(4.7), Inches(5.5), Inches(0.4),
             "⚠️ 暂定价格 · 最终根据企业情况调整", size=11,
             color=GOLD, align=PP_ALIGN.CENTER, bold=True)

    add_text(slide, Inches(0.4), Inches(5.4), Inches(5.5), Inches(1.6),
             "✅ 系统工程学方法论 5 步实施\n✅ 数据底座（不限数据量）\n✅ 2 个 AI 数字员工（按企业定制）\n✅ 30 天底座搭建\n✅ 60 天 AI 数字员工上岗\n✅ 工程师驻场陪跑",
             size=12, color=WHITE, align=PP_ALIGN.CENTER)

    # 右侧：定制化说明
    add_rounded(slide, Inches(6.1), Inches(2.4), Inches(6.8), Inches(4.7), WHITE, line=PRIMARY)
    add_text(slide, Inches(6.1), Inches(2.55), Inches(6.8), Inches(0.4),
             "🎯  为什么「按企业情况定制」？", size=15, bold=True, color=PRIMARY)
    reasons = [
        ("数据复杂度", "有的企业 1 万条数据\n有的企业 100 万条数据"),
        ("行业属性", "机械 / 纺织 / 电子 / 化工\n术语库完全不同"),
        ("业务流程", "每家企业的报价流程\n审批节点都不一样"),
        ("系统集成", "ERP / CRM / 邮件系统\n不同厂商差异巨大"),
    ]
    ry = Inches(3.1)
    for title, desc in reasons:
        add_rounded(slide, Inches(6.4), ry, Inches(6.2), Inches(0.85), LIGHT)
        add_text(slide, Inches(6.55), ry + Inches(0.1), Inches(1.6), Inches(0.6),
                 "▶ " + title, size=12, bold=True, color=PRIMARY)
        add_text(slide, Inches(8.2), ry + Inches(0.1), Inches(4.3), Inches(0.6),
                 desc, size=10, color=DARK)
        ry += Inches(0.95)


def make_commitment(slide, page_num, total):
    """30/60 承诺"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "07  COMMITMENT  ·  商务保障")
    add_page_title(slide, "30/60 双承诺",
                   "30 天底座搭建，60 天 AI 技能上线")

    # 30/60 大字
    add_rounded(slide, Inches(0.4), Inches(2.4), Inches(6.0), Inches(2.5), TEAL)
    add_text(slide, Inches(0.4), Inches(2.6), Inches(6.0), Inches(1.0),
             "30", size=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(3.6), Inches(6.0), Inches(0.4),
             "天数据底座搭建完成", size=16, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(0.4), Inches(4.0), Inches(6.0), Inches(0.5),
             "DATA HUB READY", size=10, color=GOLD, align=PP_ALIGN.CENTER, bold=True)

    add_rounded(slide, Inches(6.9), Inches(2.4), Inches(6.0), Inches(2.5), PURPLE)
    add_text(slide, Inches(6.9), Inches(2.6), Inches(6.0), Inches(1.0),
             "60", size=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(6.9), Inches(3.6), Inches(6.0), Inches(0.4),
             "天 AI 技能首批询盘", size=16, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(6.9), Inches(4.0), Inches(6.0), Inches(0.5),
             "AI SKILLS LIVE", size=10, color=GOLD, align=PP_ALIGN.CENTER, bold=True)

    # 三大保障
    guarantees = [
        ("方法论保障", "5 步法是系统工程\n可复用，可复制"),
        ("工程师陪跑", "驻场实施\n2-10 周全程"),
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
                 title, size=15, bold=True, color=TEAL)
        add_text(slide, x + Inches(0.2), gy + Inches(0.55), gw - Inches(0.4), Inches(0.8),
                 desc, size=11, color=DARK)


def make_why_us(slide, page_num, total):
    """为什么是海联智达"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "08  WHY HLZD  ·  为什么是海联智达")
    add_page_title(slide, "3 大独有优势",
                   "我们不是 SaaS 厂商，我们是企业知识数字化的工程公司")

    advantages = [
        ("方法论", "🧬", PRIMARY,
         "系统工程学方法论",
         "5 步法可复用\n不是一次性项目",
         "对标 ISO 9001 / CMMI"),
        ("工程能力", "🛠️", TEAL,
         "工程师驻场",
         "不只是远程支持\n而是手把手陪跑",
         "10+ 年数据治理经验"),
        ("AI 落地", "🤖", PURPLE,
         "2 个开箱即用技能",
         "底座 + AI 一体化\n不是分两个供应商",
         "30/60 写进合同"),
    ]
    aw = Inches(4.0)
    ag = Inches(0.2)
    ax = Inches(0.4)
    ay = Inches(2.4)
    for i, (label, icon, color, title, sub, badge) in enumerate(advantages):
        x = ax + (aw + ag) * i
        add_rounded(slide, x, ay, aw, Inches(4.6), WHITE, line=color)
        add_rect(slide, x, ay, aw, Inches(1.4), color)
        add_text(slide, x, ay + Inches(0.15), aw, Inches(0.6),
                 icon, size=42, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x, ay + Inches(0.85), aw, Inches(0.4),
                 label, size=12, color=WHITE, align=PP_ALIGN.CENTER, bold=True)
        add_text(slide, x + Inches(0.2), ay + Inches(1.6), aw - Inches(0.4), Inches(0.5),
                 title, size=18, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        add_text(slide, x + Inches(0.2), ay + Inches(2.2), aw - Inches(0.4), Inches(1.0),
                 sub, size=12, color=DARK, align=PP_ALIGN.CENTER)
        add_rounded(slide, x + Inches(0.5), ay + Inches(3.7), aw - Inches(1.0), Inches(0.6), LIGHT)
        add_text(slide, x + Inches(0.5), ay + Inches(3.7), aw - Inches(1.0), Inches(0.6),
                 badge, size=10, color=color, bold=True, align=PP_ALIGN.CENTER)


def make_contact(slide, page_num, total):
    """CTA"""
    set_bg(slide, NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.12), GOLD)
    add_text(slide, Inches(0.6), Inches(0.6), Inches(6), Inches(0.4),
             "BUSINESS COOPERATION  |  v3.6", size=10, color=GOLD, bold=True)
    add_rect(slide, Inches(0.6), Inches(1.1), Inches(2), Inches(0.04), GOLD)

    add_text(slide, Inches(0.6), Inches(1.5), Inches(12), Inches(1.0),
             "从零到一 · 30 天搭建数据底座 · 60 天 AI 数字员工上岗", size=36, bold=True, color=WHITE)
    add_text(slide, Inches(0.6), Inches(2.6), Inches(12), Inches(0.8),
             "系统工程学方法论 + 工程师驻场陪跑", size=20, color=GOLD)

    add_text(slide, Inches(0.6), Inches(3.7), Inches(12), Inches(0.5),
             "海联智达 × 定制化企业知识数字化方案", size=16, color=WHITE)

    # 3 种合作路径
    add_text(slide, Inches(0.6), Inches(4.5), Inches(12), Inches(0.4),
             "3 种合作路径", size=14, color=GOLD)
    paths = [
        ("① 直接采购", "选入门版 ¥59,800 起步\n工程师驻场 5 步实施"),
        ("② 战略合作", "联合行业头部企业\n共建数据底座联盟"),
        ("③ 渠道代理", "区域市场代理\n享受高额返点"),
    ]
    pw = Inches(3.9)
    pg = Inches(0.15)
    px = Inches(0.6)
    py = Inches(4.95)
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
        make_redefine,      # 3  重新定义
        make_methodology,   # 4  5 步法
        make_three_steps,   # 5  3 步核心动作
        make_ai_skills,     # 6  底座之上的 AI 技能
        make_business,      # 7  商务合作
        make_commitment,    # 8  30/60 承诺
        make_why_us,        # 9  为什么是我们
        make_contact,       # 10 CTA
    ]
    for i, fn in enumerate(builders):
        slide = prs.slides.add_slide(blank)
        fn(slide, i + 1, total)
        print(f"  [OK] Slide {i+1}/{total} - {fn.__name__}")

    output = r'D:\MCP_SERVER\HLZD-SALES\海联智达-数据底座-v3.6.1-Enterprise.pptx'
    if os.path.exists(output):
        os.remove(output)
    prs.save(output)
    print(f"\n[OK] PPT: {output}")
    print(f"     Size: {os.path.getsize(output)/1024:.1f} KB")


if __name__ == "__main__":
    main()
