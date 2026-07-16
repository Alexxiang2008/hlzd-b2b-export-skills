"""
海联智达 商务版 PPT 生成器
基于 v3 内容，针对商务场合（合作/招商/对外宣传/远程演示）
- 配色：深蓝 + 金色（商务感）
- 风格：克制、专业、留白多
- 适配：可发 PDF、可远程分享、无需演讲者讲解
"""

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

# 商务版配色（深蓝+金）
BIZ_NAVY = RGBColor(0x0A, 0x1F, 0x44)       # 主深蓝
BIZ_BLUE = RGBColor(0x1E, 0x3A, 0x8A)       # 次蓝
BIZ_GOLD = RGBColor(0xC9, 0xA2, 0x27)       # 金色（强调）
BIZ_GOLD_LIGHT = RGBColor(0xE8, 0xC9, 0x4D) # 浅金
BIZ_WHITE = RGBColor(0xFF, 0xFF, 0xFF)      # 白
BIZ_LIGHT = RGBColor(0xF5, 0xF6, 0xFA)      # 浅灰背景
BIZ_GRAY = RGBColor(0x6B, 0x72, 0x80)       # 灰文字
BIZ_DARK = RGBColor(0x1F, 0x29, 0x37)       # 主文字
BIZ_GREEN = RGBColor(0x2E, 0x7D, 0x32)      # 成功/增长
BIZ_BORDER = RGBColor(0xD1, 0xD5, 0xDB)     # 边框灰

FONT = "Microsoft YaHei"


# ========== 工具函数 ==========
def set_text(tf, text, size=18, bold=False, color=BIZ_DARK, align=PP_ALIGN.LEFT, font=FONT):
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


def add_text_box(slide, x, y, w, h, text, size=18, bold=False, color=BIZ_DARK,
                 align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT, italic=False):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    set_text(tf, text, size, bold, color, align, font)
    if italic:
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.italic = True
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


def add_line(slide, x1, y1, x2, y2, color=BIZ_GOLD, weight=1.5):
    s = slide.shapes.add_connector(1, x1, y1, x2, y2)
    s.line.color.rgb = color
    s.line.width = Pt(weight)
    return s


def set_bg(slide, color=BIZ_WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_biz_header(slide, page_num, total, section):
    """商务版页头：克制、专业"""
    # 顶部细金线
    add_line(slide, Inches(0.6), Inches(0.45), Inches(12.7), Inches(0.45), BIZ_GOLD, 0.5)
    # 左：品牌
    add_text_box(slide, Inches(0.6), Inches(0.18), Inches(3), Inches(0.3),
                 "海联智达  ·  HLZD", size=10, color=BIZ_GRAY)
    # 右：页码
    add_text_box(slide, Inches(11.0), Inches(0.18), Inches(1.7), Inches(0.3),
                 f"{page_num:02d} / {total:02d}", size=10, color=BIZ_GRAY, align=PP_ALIGN.RIGHT)
    # 章节名（小标）
    add_text_box(slide, Inches(0.6), Inches(0.6), Inches(12), Inches(0.4),
                 section, size=12, color=BIZ_GOLD, bold=True)


def add_biz_footer(slide):
    """商务版页脚"""
    add_line(slide, Inches(0.6), Inches(7.1), Inches(12.7), Inches(7.1), BIZ_BORDER, 0.5)
    add_text_box(slide, Inches(0.6), Inches(7.2), Inches(12), Inches(0.3),
                 "海联智达  |  让中国工厂做全世界的生意  |  商务版 v3.1",
                 size=9, color=BIZ_GRAY)


def add_page_title(slide, title, subtitle=None):
    """统一页面标题"""
    # 主标题
    add_text_box(slide, Inches(0.6), Inches(1.2), Inches(12), Inches(0.8),
                 title, size=32, bold=True, color=BIZ_NAVY)
    # 金色装饰短线
    add_rect(slide, Inches(0.6), Inches(2.0), Inches(0.6), Inches(0.04), BIZ_GOLD)
    # 副标题
    if subtitle:
        add_text_box(slide, Inches(0.6), Inches(2.1), Inches(12), Inches(0.5),
                     subtitle, size=14, color=BIZ_GRAY)


# ========== 12 张幻灯片 ==========
def make_cover(slide, page_num, total):
    """第 1 页：商务版封面"""
    set_bg(slide, BIZ_NAVY)
    # 顶部金色装饰条
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), BIZ_GOLD)
    # 商务版标识
    add_text_box(slide, Inches(0.6), Inches(0.6), Inches(4), Inches(0.4),
                 "BUSINESS PRESENTATION  |  商务版", size=11, color=BIZ_GOLD, bold=True)
    # 装饰金线
    add_line(slide, Inches(0.6), Inches(1.2), Inches(2.0), Inches(1.2), BIZ_GOLD, 2)
    # 大标题
    add_text_box(slide, Inches(0.6), Inches(1.8), Inches(12), Inches(1.4),
                 "让中国工厂", size=58, bold=True, color=BIZ_WHITE)
    add_text_box(slide, Inches(0.6), Inches(2.8), Inches(12), Inches(1.4),
                 "做全世界的生意", size=58, bold=True, color=BIZ_GOLD)
    # 副标题
    add_text_box(slide, Inches(0.6), Inches(4.5), Inches(12), Inches(0.6),
                 "海联智达 × 外贸 AI 赋能方案", size=24, color=BIZ_WHITE)
    add_text_box(slide, Inches(0.6), Inches(5.0), Inches(12), Inches(0.4),
                 "HaiLian ZhiDa  ·  Cross-border Trade AI Platform", size=12,
                 color=BIZ_GOLD_LIGHT, italic=True)
    # 核心承诺
    add_text_box(slide, Inches(0.6), Inches(6.0), Inches(12), Inches(0.5),
                 "大厂做宽，我们做深；大厂卖工具，我们给结果。", size=16,
                 color=BIZ_GOLD_LIGHT)
    # 底部信息
    add_text_box(slide, Inches(0.6), Inches(6.8), Inches(12), Inches(0.3),
                 "2026.06  |  商务合作版", size=10, color=BIZ_GRAY)


def make_overview(slide, page_num, total):
    """第 2 页：商务概览（替代销售版钩子页）"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "01  EXECUTIVE OVERVIEW")
    add_page_title(slide, "方案概览", "5 分钟读懂海联智达")

    # 3 个核心数字
    add_text_box(slide, Inches(0.6), Inches(2.8), Inches(12), Inches(0.4),
                 "公司核心数据", size=16, bold=True, color=BIZ_DARK)
    metrics = [
        ("30 天", "系统搭建周期"),
        ("60 天", "首批询盘产出"),
        ("4 大行业", "机械/纺织/电子/化工"),
        ("3 档套餐", "¥59,800 起"),
    ]
    mw = Inches(2.95)
    mg = Inches(0.15)
    mx = Inches(0.6)
    my = Inches(3.3)
    for i, (num, desc) in enumerate(metrics):
        x = mx + (mw + mg) * i
        add_rounded(slide, x, my, mw, Inches(1.5), BIZ_LIGHT, line=BIZ_BORDER)
        add_text_box(slide, x, my + Inches(0.15), mw, Inches(0.7), num,
                     size=32, bold=True, color=BIZ_GOLD, align=PP_ALIGN.CENTER)
        add_text_box(slide, x, my + Inches(0.85), mw, Inches(0.5), desc,
                     size=12, color=BIZ_DARK, align=PP_ALIGN.CENTER)

    # 4 大业务板块
    add_text_box(slide, Inches(0.6), Inches(5.1), Inches(12), Inches(0.4),
                 "业务板块", size=16, bold=True, color=BIZ_DARK)
    sectors = [
        ("数字大脑", "SAG 事件图谱\n+ 行业 Know-How"),
        ("Bot-Agent", "10-50 个数字员工\n7×24 在线"),
        ("Skills-Map", "企业能力图谱\n动态编排"),
        ("上门陪跑", "数据清洗 + Skill 定制\n+ 工作流"),
    ]
    sw = Inches(2.95)
    sg = Inches(0.15)
    sx = Inches(0.6)
    sy = Inches(5.6)
    for i, (title, desc) in enumerate(sectors):
        x = sx + (sw + sg) * i
        add_rect(slide, x, sy, sw, Inches(1.2), BIZ_NAVY)
        add_text_box(slide, x + Inches(0.2), sy + Inches(0.1), sw - Inches(0.4), Inches(0.4),
                     title, size=15, bold=True, color=BIZ_GOLD, align=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.2), sy + Inches(0.55), sw - Inches(0.4), Inches(0.6),
                     desc, size=11, color=BIZ_WHITE, align=PP_ALIGN.CENTER)
    add_biz_footer(slide)


def make_market(slide, page_num, total):
    """第 3 页：市场洞察"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "02  MARKET INSIGHT")
    add_page_title(slide, "市场洞察", "外贸行业正在经历 4 大结构性变化")

    insights = [
        ("生态升级", "B2B → A2A", "博弈维度从企业对企业升级为生态对生态", BIZ_BLUE),
        ("合规趋严", "出海难在「进门」", "政策、资质、舆情、标准成为核心门槛", BIZ_NAVY),
        ("数据觉醒", "「数据裸奔」终结", "80% 工厂仍凭感觉拍板，市场洞察成瓶颈", BIZ_GOLD),
        ("人才稀缺", "招不来/留不住/用不对", "复合型外贸人才成为稀缺资源", BIZ_GRAY),
    ]
    iw = Inches(5.95)
    ig = Inches(0.2)
    ix = Inches(0.6)
    iy = Inches(2.8)
    for i, (title, sub, desc, color) in enumerate(insights):
        row = i // 2
        col = i % 2
        x = ix + (iw + ig) * col
        y = iy + Inches(1.85) * row
        add_rounded(slide, x, y, iw, Inches(1.7), BIZ_LIGHT, line=BIZ_BORDER)
        # 左侧色条
        add_rect(slide, x, y, Inches(0.12), Inches(1.7), color)
        # 标题
        add_text_box(slide, x + Inches(0.3), y + Inches(0.15), iw - Inches(0.4), Inches(0.4),
                     title, size=16, bold=True, color=BIZ_NAVY)
        # 副标题
        add_text_box(slide, x + Inches(0.3), y + Inches(0.6), iw - Inches(0.4), Inches(0.4),
                     sub, size=14, bold=True, color=color)
        # 描述
        add_text_box(slide, x + Inches(0.3), y + Inches(1.05), iw - Inches(0.4), Inches(0.6),
                     desc, size=12, color=BIZ_DARK)
    add_biz_footer(slide)


def make_solution(slide, page_num, total):
    """第 4 页：解决方案架构"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "03  SOLUTION")
    add_page_title(slide, "解决方案", "数据大脑 + 重交付 = AI 真正落地")

    # 4 层架构
    add_text_box(slide, Inches(0.6), Inches(2.7), Inches(12), Inches(0.4),
                 "4 层能力架构", size=16, bold=True, color=BIZ_DARK)
    layers = [
        ("L1  基础设施", "独立服务器  |  多国节点  |  数据加密", BIZ_NAVY),
        ("L2  数据大脑", "SAG 事件图谱  |  行业术语库  |  持续进化", BIZ_BLUE),
        ("L3  智能体矩阵", "Bot-Agent ×10-50  |  多智能体路由  |  Skills-Map", BIZ_GOLD),
        ("L4  价值交付", "全链路赋能  |  上门陪跑  |  7×24 工程师", BIZ_GREEN),
    ]
    lw = Inches(2.95)
    lg = Inches(0.15)
    lx = Inches(0.6)
    ly = Inches(3.2)
    for i, (title, desc, color) in enumerate(layers):
        x = lx + (lw + lg) * i
        add_rect(slide, x, ly, lw, Inches(0.6), color)
        add_text_box(slide, x + Inches(0.2), ly, lw - Inches(0.4), Inches(0.6),
                     title, size=14, bold=True, color=BIZ_WHITE, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)
        add_rect(slide, x, ly + Inches(0.6), lw, Inches(1.3), BIZ_LIGHT, line=BIZ_BORDER)
        add_text_box(slide, x + Inches(0.2), ly + Inches(0.7), lw - Inches(0.4), Inches(1.1),
                     desc, size=11, color=BIZ_DARK, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)

    # 价值链
    add_text_box(slide, Inches(0.6), Inches(5.5), Inches(12), Inches(0.4),
                 "全链路价值赋能", size=16, bold=True, color=BIZ_DARK)
    stages = ["获客", "跟进", "谈判", "成单", "复购"]
    sw = Inches(2.4)
    sg = Inches(0.05)
    sx = Inches(0.6)
    sy = Inches(6.0)
    for i, stage in enumerate(stages):
        x = sx + (sw + sg) * i
        add_rounded(slide, x, sy, sw, Inches(0.7), BIZ_NAVY)
        add_text_box(slide, x, sy, sw, Inches(0.7), f"{i+1}. {stage}", size=14, bold=True,
                     color=BIZ_GOLD, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < 4:
            add_text_box(slide, x + sw - Inches(0.1), sy + Inches(0.25), Inches(0.2),
                         Inches(0.2), "→", size=18, bold=True, color=BIZ_GOLD,
                         align=PP_ALIGN.CENTER)
    add_biz_footer(slide)


def make_cases(slide, page_num, total):
    """第 5 页：客户案例（占位 + 通用框架）"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "04  CLIENT SUCCESS")
    add_page_title(slide, "客户成功", "已服务 20+ 行业头部工厂（详细数据需商务洽谈）")

    # 3 个案例占位
    cases = [
        ("机械制造", "年营收 8,000 万\n主攻欧美市场", "AI 数字大脑 + 工程师上门", "30 天搭建 / 60 天首批询盘"),
        ("纺织服装", "年营收 1.2 亿\n主攻东南亚/中东", "行业术语库 + 趋势分析", "30 天搭建 / 60 天首批询盘"),
        ("电子电器", "年营收 5,000 万\n主攻北美市场", "认证标准匹配 + 多语言文档", "30 天搭建 / 60 天首批询盘"),
    ]
    cw = Inches(3.95)
    cg = Inches(0.15)
    cx = Inches(0.6)
    cy = Inches(2.8)
    for i, (ind, scale, sol, time) in enumerate(cases):
        x = cx + (cw + cg) * i
        add_rounded(slide, x, cy, cw, Inches(3.5), BIZ_LIGHT, line=BIZ_BORDER)
        # 顶部色条
        add_rect(slide, x, cy, cw, Inches(0.5), BIZ_NAVY)
        add_text_box(slide, x, cy, cw, Inches(0.5), f"案例 {chr(65+i)}  ·  {ind}", size=16,
                     bold=True, color=BIZ_GOLD, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)
        # 规模
        add_text_box(slide, x + Inches(0.3), cy + Inches(0.7), cw - Inches(0.6), Inches(0.8),
                     "【客户规模】\n" + scale, size=12, color=BIZ_DARK)
        # 方案
        add_text_box(slide, x + Inches(0.3), cy + Inches(1.7), cw - Inches(0.6), Inches(0.8),
                     "【解决方案】\n" + sol, size=12, color=BIZ_DARK)
        # 时间
        add_text_box(slide, x + Inches(0.3), cy + Inches(2.7), cw - Inches(0.6), Inches(0.5),
                     "【交付周期】  " + time, size=12, bold=True, color=BIZ_GOLD)
        # 详细数据提示
        add_text_box(slide, x + Inches(0.3), cy + Inches(3.1), cw - Inches(0.6), Inches(0.3),
                     "* 详细 ROI 数据商务洽谈时提供", size=9, color=BIZ_GRAY, italic=True)
    add_biz_footer(slide)


def make_advantage(slide, page_num, total):
    """第 6 页：核心优势"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "05  COMPETITIVE EDGE")
    add_page_title(slide, "核心优势", "5 维竞争壁垒，对比大厂与通用 SaaS")

    headers = ["维度", "海联智达", "通用大厂", "通用 SaaS"]
    rows = [
        ["技术架构", "SAG 多跳推理", "RAG 单跳", "营销自动化"],
        ["行业深度", "4 大行业专精", "通用语料", "无行业属性"],
        ["服务模式", "重交付 + 上门", "客户自研", "文档自助"],
        ["数据安全", "独立部署 + 多国", "平台统一", "数据出境风险"],
        ["效果承诺", "30/60 写进合同", "工具上线即结束", "工具上线即结束"],
    ]
    tx = Inches(0.6)
    ty = Inches(2.8)
    rh = Inches(0.6)
    cw_list = [Inches(2.0), Inches(3.5), Inches(3.5), Inches(3.0)]
    # 表头
    x = tx
    for j, h in enumerate(headers):
        bg = BIZ_NAVY if j == 0 else (BIZ_GOLD if j == 1 else BIZ_GRAY)
        add_rect(slide, x, ty, cw_list[j], rh, bg)
        add_text_box(slide, x + Inches(0.15), ty, cw_list[j] - Inches(0.3), rh, h,
                     size=14, bold=True, color=BIZ_WHITE, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)
        x += cw_list[j]
    # 数据行
    for i, row in enumerate(rows):
        y = ty + rh * (i + 1)
        x = tx
        for j, cell in enumerate(row):
            bg = BIZ_LIGHT if i % 2 == 0 else BIZ_WHITE
            add_rect(slide, x, y, cw_list[j], rh, bg, line=BIZ_BORDER)
            color = BIZ_NAVY if j == 0 else (BIZ_GOLD if j == 1 else BIZ_DARK)
            bold = (j == 1)
            add_text_box(slide, x + Inches(0.15), y, cw_list[j] - Inches(0.3), rh, cell,
                         size=13, bold=bold, color=color, align=PP_ALIGN.CENTER,
                         anchor=MSO_ANCHOR.MIDDLE)
            x += cw_list[j]
    # 底部金句
    add_text_box(slide, Inches(0.6), Inches(6.5), Inches(12), Inches(0.4),
                 "—— 我们不只卖软件，而是卖「数据基建 + 组织赋能」的全程陪跑服务",
                 size=14, color=BIZ_GOLD, align=PP_ALIGN.CENTER, italic=True)
    add_biz_footer(slide)


def make_industries(slide, page_num, total):
    """第 7 页：行业专精"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "06  INDUSTRY EXPERTISE")
    add_page_title(slide, "行业专精", "机械 / 纺织 / 电子 / 化工 4 大行业深度 Know-How")

    industries = [
        ("机械制造", "数控机床\n工业配件\n定制设备", "技术规格翻译\nCE/UL/RoHS 合规"),
        ("纺织服装", "面料辅料\n成衣定制\nOEM/ODM", "流行趋势分析\nBSCI/OEKO-TEX 认证"),
        ("电子电器", "消费电子\n零部件\nIoT 设备", "FCC/CE 认证匹配\n多语言说明书"),
        ("化工材料", "工业原料\n添加剂\n涂料", "MSDS 自动生成\nREACH/危险品合规"),
    ]
    iw = Inches(2.95)
    ig = Inches(0.15)
    ix = Inches(0.6)
    iy = Inches(2.8)
    for i, (name, scene, skill) in enumerate(industries):
        x = ix + (iw + ig) * i
        add_rounded(slide, x, iy, iw, Inches(3.4), BIZ_LIGHT, line=BIZ_BORDER)
        # 行业色块
        add_rect(slide, x, iy, iw, Inches(0.6), BIZ_NAVY)
        add_text_box(slide, x, iy, iw, Inches(0.6), name, size=18, bold=True,
                     color=BIZ_GOLD, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        # 场景
        add_text_box(slide, x + Inches(0.25), iy + Inches(0.8), iw - Inches(0.5),
                     Inches(0.4), "核心场景", size=11, color=BIZ_GRAY, bold=True)
        add_text_box(slide, x + Inches(0.25), iy + Inches(1.2), iw - Inches(0.5),
                     Inches(1.0), scene, size=13, color=BIZ_DARK)
        # 能力
        add_text_box(slide, x + Inches(0.25), iy + Inches(2.3), iw - Inches(0.5),
                     Inches(0.4), "专属能力", size=11, color=BIZ_GRAY, bold=True)
        add_text_box(slide, x + Inches(0.25), iy + Inches(2.65), iw - Inches(0.5),
                     Inches(0.7), skill, size=12, bold=True, color=BIZ_GOLD)
    add_text_box(slide, Inches(0.6), Inches(6.4), Inches(12), Inches(0.4),
                 "其他行业可定制（约 60 天）  ·  行业术语库持续迭代",
                 size=12, color=BIZ_GRAY, align=PP_ALIGN.CENTER, italic=True)
    add_biz_footer(slide)


def make_pricing(slide, page_num, total):
    """第 8 页：商务合作（3 档套餐）"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "07  COOPERATION MODEL")
    add_page_title(slide, "合作模式", "3 档梯度 · 灵活选择")

    packages = [
        ("入门版", "¥59,800", "Standard", BIZ_BLUE,
         ["数字大脑（自进化）", "Bot-Agent ×10 席", "美国独立网络", "7×24 专属支持", "统一登录/操作追溯"]),
        ("基础版", "¥99,800", "Professional", BIZ_NAVY,
         ["入门版全部配置", "+ 知识冷启动服务", "+ 5 国服务器可选", "+ Bot-Agent ×25 席", "+ 10 人组织"]),
        ("旗舰版", "¥188,000", "Enterprise", BIZ_GOLD,
         ["基础版全部配置", "+ 知识库进阶启动", "+ 定制 Skill + 工作流", "+ 21 国服务器可选", "+ 工程师上门服务"]),
    ]
    pw = Inches(3.95)
    pg = Inches(0.15)
    px = Inches(0.6)
    py = Inches(2.7)
    for i, (name, price, eng, color, features) in enumerate(packages):
        x = px + (pw + pg) * i
        # 卡片
        add_rounded(slide, x, py, pw, Inches(4.1), BIZ_LIGHT, line=BIZ_BORDER)
        # 顶部色块
        add_rect(slide, x, py, pw, Inches(1.1), color)
        # 名称
        add_text_box(slide, x, py + Inches(0.1), pw, Inches(0.4), name,
                     size=18, bold=True, color=BIZ_WHITE, align=PP_ALIGN.CENTER)
        # 英文
        add_text_box(slide, x, py + Inches(0.5), pw, Inches(0.3), eng.upper(),
                     size=10, color=BIZ_GOLD_LIGHT, align=PP_ALIGN.CENTER)
        # 价格
        add_text_box(slide, x, py + Inches(0.8), pw, Inches(0.4), price,
                     size=22, bold=True, color=BIZ_WHITE, align=PP_ALIGN.CENTER)
        # 功能列表
        fy = py + Inches(1.3)
        for feat in features:
            add_text_box(slide, x + Inches(0.3), fy, pw - Inches(0.6), Inches(0.4),
                         "✓  " + feat, size=12, color=BIZ_DARK)
            fy += Inches(0.45)
    add_biz_footer(slide)


def make_guarantee(slide, page_num, total):
    """第 9 页：商务保障"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "08  OUR COMMITMENT")
    add_page_title(slide, "商务保障", "30/60 承诺 + 数据安全 + 7×24 服务")

    # 30/60 大字
    add_rect(slide, Inches(0.6), Inches(2.7), Inches(5.95), Inches(2.0), BIZ_NAVY)
    add_text_box(slide, Inches(0.6), Inches(2.85), Inches(5.95), Inches(0.7), "30",
                 size=64, bold=True, color=BIZ_GOLD, align=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(0.6), Inches(3.5), Inches(5.95), Inches(0.4), "天系统搭建",
                 size=16, color=BIZ_WHITE, align=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(0.6), Inches(3.95), Inches(5.95), Inches(0.5),
                 "SYSTEM DEPLOYMENT", size=10, color=BIZ_GOLD_LIGHT,
                 align=PP_ALIGN.CENTER, italic=True)

    add_rect(slide, Inches(6.75), Inches(2.7), Inches(5.95), Inches(2.0), BIZ_GOLD)
    add_text_box(slide, Inches(6.75), Inches(2.85), Inches(5.95), Inches(0.7), "60",
                 size=64, bold=True, color=BIZ_NAVY, align=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(6.75), Inches(3.5), Inches(5.95), Inches(0.4), "天首批询盘",
                 size=16, color=BIZ_NAVY, align=PP_ALIGN.CENTER, bold=True)
    add_text_box(slide, Inches(6.75), Inches(3.95), Inches(5.95), Inches(0.5),
                 "FIRST INQUIRIES DELIVERED", size=10, color=BIZ_NAVY,
                 align=PP_ALIGN.CENTER, italic=True)

    # 三大保障
    add_text_box(slide, Inches(0.6), Inches(5.0), Inches(12), Inches(0.4),
                 "服务体系", size=16, bold=True, color=BIZ_DARK)
    guarantees = [
        ("数据安全", "独立部署\nTLS 1.3 + AES-256\n符合 GDPR / 中国法规"),
        ("7×24 工程师", "专属服务群\n1 小时首次响应\n月度复盘"),
        ("效果承诺", "30/60 写进合同\n不达标免费延期\n至达标"),
    ]
    gw = Inches(3.95)
    gg = Inches(0.15)
    gx = Inches(0.6)
    gy = Inches(5.5)
    for i, (title, desc) in enumerate(guarantees):
        x = gx + (gw + gg) * i
        add_rounded(slide, x, gy, gw, Inches(1.4), BIZ_LIGHT, line=BIZ_BORDER)
        add_text_box(slide, x + Inches(0.3), gy + Inches(0.1), gw - Inches(0.6), Inches(0.4),
                     title, size=15, bold=True, color=BIZ_GOLD)
        add_text_box(slide, x + Inches(0.3), gy + Inches(0.55), gw - Inches(0.6), Inches(0.8),
                     desc, size=11, color=BIZ_DARK)
    add_biz_footer(slide)


def make_team(slide, page_num, total):
    """第 10 页：团队与公司（商务版新增）"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "09  OUR TEAM")
    add_page_title(slide, "核心团队", "出海老兵 × 大厂 AI 架构师 × 科学院专家")

    members = [
        ("创始团队", "出海老兵", "10+ 年外贸业务经验\n深耕欧美/东南亚/中东市场"),
        ("技术团队", "大厂 AI 架构师", "曾任职于头部互联网公司\n主导过亿级用户 AI 产品"),
        ("科研团队", "科学院专家", "自然语言处理 / 知识图谱\n前沿 AI 研究能力"),
    ]
    mw = Inches(3.95)
    mg = Inches(0.15)
    mx = Inches(0.6)
    my = Inches(2.8)
    for i, (cat, role, desc) in enumerate(members):
        x = mx + (mw + mg) * i
        add_rounded(slide, x, my, mw, Inches(2.5), BIZ_LIGHT, line=BIZ_BORDER)
        # 左侧金色色条
        add_rect(slide, x, my, Inches(0.15), Inches(2.5), BIZ_GOLD)
        # 分类
        add_text_box(slide, x + Inches(0.4), my + Inches(0.2), mw - Inches(0.6), Inches(0.4),
                     cat, size=14, bold=True, color=BIZ_GOLD)
        # 角色
        add_text_box(slide, x + Inches(0.4), my + Inches(0.7), mw - Inches(0.6), Inches(0.5),
                     role, size=18, bold=True, color=BIZ_NAVY)
        # 描述
        add_text_box(slide, x + Inches(0.4), my + Inches(1.3), mw - Inches(0.6), Inches(1.0),
                     desc, size=12, color=BIZ_DARK)

    # 公司愿景
    add_rounded(slide, Inches(0.6), Inches(5.6), Inches(12.1), Inches(1.3), BIZ_NAVY)
    add_text_box(slide, Inches(0.6), Inches(5.7), Inches(12.1), Inches(0.4),
                 "OUR MISSION  ·  我们的使命", size=11, color=BIZ_GOLD,
                 align=PP_ALIGN.CENTER, bold=True)
    add_text_box(slide, Inches(0.6), Inches(6.1), Inches(12.1), Inches(0.7),
                 "用 AI 把中国工业品产业链上的工厂连成联盟，把新时代市场规则（数据 / 流量 / AI）交到工厂手里。",
                 size=16, color=BIZ_WHITE, align=PP_ALIGN.CENTER, bold=True)
    add_biz_footer(slide)


def make_contact(slide, page_num, total):
    """第 11 页：商务合作邀请"""
    set_bg(slide, BIZ_NAVY)
    # 顶部金线
    add_line(slide, Inches(0.6), Inches(0.6), Inches(12.7), Inches(0.6), BIZ_GOLD, 1.5)
    # 标题
    add_text_box(slide, Inches(0.6), Inches(1.0), Inches(12), Inches(0.4),
                 "BUSINESS COOPERATION", size=12, color=BIZ_GOLD, bold=True)
    add_text_box(slide, Inches(0.6), Inches(1.5), Inches(12), Inches(1.0),
                 "开启合作", size=54, bold=True, color=BIZ_WHITE)
    add_text_box(slide, Inches(0.6), Inches(2.7), Inches(12), Inches(0.6),
                 "让我们用 30 天为您搭建数据大脑，60 天见证首批询盘", size=18,
                 color=BIZ_GOLD_LIGHT)

    # 3 种合作路径
    add_text_box(slide, Inches(0.6), Inches(3.8), Inches(12), Inches(0.4),
                 "3 种合作路径", size=16, bold=True, color=BIZ_GOLD)
    paths = [
        ("①  直接采购", "选购入门版/基础版/旗舰版\n签约即启动"),
        ("②  战略合作", "联合行业头部工厂\n共建国贸 AI 联盟"),
        ("③  渠道代理", "区域市场代理\n享受高额返点"),
    ]
    pw = Inches(3.95)
    pg = Inches(0.15)
    px = Inches(0.6)
    py = Inches(4.3)
    for i, (title, desc) in enumerate(paths):
        x = px + (pw + pg) * i
        add_rounded(slide, x, py, pw, Inches(1.5), BIZ_NAVY, line=BIZ_GOLD)
        add_text_box(slide, x + Inches(0.3), py + Inches(0.15), pw - Inches(0.6), Inches(0.5),
                     title, size=18, bold=True, color=BIZ_GOLD)
        add_text_box(slide, x + Inches(0.3), py + Inches(0.7), pw - Inches(0.6), Inches(0.7),
                     desc, size=12, color=BIZ_WHITE)
    # CTA
    add_text_box(slide, Inches(0.6), Inches(6.3), Inches(12), Inches(0.5),
                 "📧  business@hailian-zhida.com  |  📞  400-XXX-XXXX",
                 size=18, color=BIZ_WHITE, align=PP_ALIGN.CENTER, bold=True)
    add_text_box(slide, Inches(0.6), Inches(6.9), Inches(12), Inches(0.3),
                 "期待与您共建国贸 AI 新生态", size=12, color=BIZ_GOLD_LIGHT,
                 align=PP_ALIGN.CENTER, italic=True)


def make_roadmap(slide, page_num, total):
    """第 12 页：12 个月路线图（商务版收尾）"""
    set_bg(slide)
    add_biz_header(slide, page_num, total, "10  ROADMAP")
    add_page_title(slide, "12 个月路线图", "从签约到规模化的完整路径")

    phases = [
        ("M1", "启动期", "需求对齐\n数据清洗\n系统搭建", BIZ_BLUE),
        ("M2", "冷启动", "首批询盘\n行业术语库\n业务流程调优", BIZ_NAVY),
        ("M3-M4", "规模化", "Bot-Agent 扩容\n跨部门赋能\n数据闭环", BIZ_GOLD),
        ("M5-M6", "效果验证", "询盘稳定增长\nROI 测算\n案例复制", BIZ_GREEN),
        ("M7-M12", "战略升级", "AI 联盟对接\n上下游生态\n全球化布局", BIZ_GRAY),
    ]
    pw = Inches(2.4)
    pg = Inches(0.1)
    px = Inches(0.6)
    py = Inches(2.8)
    for i, (month, phase, items, color) in enumerate(phases):
        x = px + (pw + pg) * i
        # 阶段色块
        add_rect(slide, x, py, pw, Inches(0.7), color)
        add_text_box(slide, x, py, pw, Inches(0.7), month, size=18, bold=True,
                     color=BIZ_WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        # 阶段名
        add_rect(slide, x, py + Inches(0.7), pw, Inches(0.5), BIZ_GOLD)
        add_text_box(slide, x, py + Inches(0.7), pw, Inches(0.5), phase, size=14, bold=True,
                     color=BIZ_NAVY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        # 任务
        add_rounded(slide, x, py + Inches(1.2), pw, Inches(2.0), BIZ_LIGHT, line=BIZ_BORDER)
        add_text_box(slide, x + Inches(0.2), py + Inches(1.3), pw - Inches(0.4), Inches(1.8),
                     items, size=12, color=BIZ_DARK, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)

    # 关键里程碑
    add_rounded(slide, Inches(0.6), Inches(6.1), Inches(12.1), Inches(0.8), BIZ_NAVY)
    add_text_box(slide, Inches(0.6), Inches(6.15), Inches(12.1), Inches(0.4),
                 "关键里程碑", size=11, color=BIZ_GOLD, align=PP_ALIGN.CENTER, bold=True)
    add_text_box(slide, Inches(0.6), Inches(6.5), Inches(12.1), Inches(0.4),
                 "M2 首批询盘  |  M4 询盘稳定  |  M6 ROI 验证  |  M12 战略升级",
                 size=14, color=BIZ_WHITE, align=PP_ALIGN.CENTER, bold=True)
    add_biz_footer(slide)


# ========== 主流程 ==========
def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    total = 12
    builders = [
        make_cover,        # 1  商务封面
        make_overview,     # 2  概览（替代销售版钩子）
        make_market,       # 3  市场洞察
        make_solution,     # 4  解决方案
        make_cases,        # 5  客户成功
        make_advantage,    # 6  核心优势
        make_industries,   # 7  行业专精
        make_pricing,      # 8  合作模式
        make_guarantee,    # 9  商务保障
        make_team,         # 10 团队（商务版新增）
        make_contact,      # 11 合作邀请（替代销售版 CTA）
        make_roadmap,      # 12 12 个月路线图（商务版新增）
    ]
    for i, fn in enumerate(builders):
        slide = prs.slides.add_slide(blank)
        fn(slide, i + 1, total)
        print(f"  [OK] Slide {i+1}/{total} - {fn.__name__}")

    output = "D:/MCP_SERVER/HLZD-SALES/海联智达-商务版-v3.1.pptx"
    prs.save(output)
    print(f"\n[SUCCESS] Business PPT generated: {output}")
    print(f"   Total slides: {total}")
    print(f"   Style: Navy + Gold, professional")


if __name__ == "__main__":
    main()
