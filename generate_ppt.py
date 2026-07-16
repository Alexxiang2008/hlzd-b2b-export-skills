"""
海联智达 PPT 生成器 v3
基于 Obsidian Markdown v3 文档生成 16:9 PowerPoint
场景：工厂老板 30-60 分钟一对一销售
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ========== 设计常量 ==========
SLIDE_W = Inches(13.333)  # 16:9
SLIDE_H = Inches(7.5)

# 品牌色
BRAND_BLUE = RGBColor(0x1F, 0x6F, 0xEB)       # 主色
BRAND_GREEN = RGBColor(0x2E, 0xA0, 0x43)      # 增长/承诺
BRAND_RED = RGBColor(0xF8, 0x51, 0x49)        # 警告/痛点
BRAND_DARK = RGBColor(0x0D, 0x11, 0x17)       # 标题
BRAND_GRAY = RGBColor(0x6E, 0x76, 0x81)       # 次要文字
BRAND_LIGHT = RGBColor(0xF6, 0xF8, 0xFA)      # 背景灰
BRAND_PURPLE = RGBColor(0x89, 0x57, 0xE5)     # 旗舰版
BRAND_GOLD = RGBColor(0xD2, 0x9E, 0x2D)       # 钩子强调

# 字体
FONT = "Microsoft YaHei"
FONT_BOLD = "Microsoft YaHei"

# ========== 工具函数 ==========
def set_text(tf, text, size=18, bold=False, color=BRAND_DARK, align=PP_ALIGN.LEFT, font=FONT):
    """设置文本框文字"""
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    # 设置中文字体
    rPr = run._r.get_or_add_rPr()
    eastAsia = etree.SubElement(rPr, qn('a:ea'))
    eastAsia.set('typeface', font)


def add_text_box(slide, x, y, w, h, text, size=18, bold=False, color=BRAND_DARK,
                 align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT):
    """添加文本框"""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    set_text(tf, text, size, bold, color, align, font)
    return tb


def add_rect(slide, x, y, w, h, fill, line=None):
    """添加矩形"""
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    s.shadow.inherit = False
    return s


def add_rounded(slide, x, y, w, h, fill, line=None, radius_adj=0.1):
    """添加圆角矩形"""
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.5)
    s.shadow.inherit = False
    return s


def add_header(slide, page_num, total, section_name, page_title):
    """页头：品牌 + 章节名 + 页码"""
    # 左上角：品牌名
    add_text_box(slide, Inches(0.4), Inches(0.25), Inches(3), Inches(0.4),
                 "海联智达", size=14, bold=True, color=BRAND_BLUE)
    # 章节名（顶部居中）
    add_text_box(slide, Inches(0.4), Inches(0.6), Inches(12.5), Inches(0.4),
                 f"{section_name}  ·  {page_title}", size=12, color=BRAND_GRAY)
    # 页码（右上）
    add_text_box(slide, Inches(12.0), Inches(0.25), Inches(1.2), Inches(0.4),
                 f"{page_num} / {total}", size=12, color=BRAND_GRAY, align=PP_ALIGN.RIGHT)
    # 顶部装饰条
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.15), BRAND_BLUE)


def add_footer(slide, slogan="让中国工厂做全世界的生意"):
    """页脚"""
    add_text_box(slide, Inches(0.4), Inches(7.1), Inches(12.5), Inches(0.3),
                 f"海联智达 | {slogan}", size=9, color=BRAND_GRAY)


def set_bg(slide, color=RGBColor(0xFF, 0xFF, 0xFF)):
    """设置纯色背景"""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


# ========== 12 张幻灯片 ==========
def make_cover(slide, page_num, total):
    """第 1 页：封面"""
    set_bg(slide, BRAND_DARK)
    # 大标题
    add_text_box(slide, Inches(0.8), Inches(2.0), Inches(11.5), Inches(1.2),
                 "让中国工厂", size=72, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    add_text_box(slide, Inches(0.8), Inches(3.1), Inches(11.5), Inches(1.2),
                 "做全世界的生意", size=72, bold=True, color=BRAND_BLUE)
    # 副标题
    add_text_box(slide, Inches(0.8), Inches(4.6), Inches(11.5), Inches(0.6),
                 "海联智达 × 外贸 AI 赋能方案", size=24, color=RGBColor(0xCC, 0xD0, 0xD6))
    # 金句
    add_text_box(slide, Inches(0.8), Inches(5.5), Inches(11.5), Inches(0.5),
                 "大厂做宽，我们做深；大厂卖工具，我们给结果。", size=18,
                 color=BRAND_GREEN)
    # 装饰
    add_rect(slide, Inches(0.8), Inches(1.7), Inches(0.8), Inches(0.06), BRAND_GREEN)
    # 底部信息
    add_text_box(slide, Inches(0.8), Inches(6.8), Inches(11.5), Inches(0.4),
                 "工厂老板一对一销售版  |  2026.06", size=11,
                 color=RGBColor(0x8B, 0x92, 0x9B))


def make_hook(slide, page_num, total):
    """第 2 页：钩子页（3 个惊人数字）"""
    set_bg(slide)
    add_header(slide, page_num, total, "1. 钩子页", "30 秒抓住老板注意力")
    # 大标题
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.7),
                 "3 个让老板坐不住的数字", size=36, bold=True, color=BRAND_DARK)
    # 3 个数字卡片
    cards = [
        ("80%", "中国外贸工厂仍处于「数据裸奔」状态", BRAND_RED, "老板拍脑袋决策"),
        ("30天", "企业级AI数字大脑搭建，提效100%", BRAND_BLUE, "系统级变革"),
        ("60天", "首批符合画像的询盘产出", BRAND_GREEN, "效果可写入合同"),
    ]
    card_w = Inches(3.8)
    gap = Inches(0.3)
    start_x = Inches(0.8)
    for i, (num, desc, color, sub) in enumerate(cards):
        x = start_x + (card_w + gap) * i
        # 卡片背景
        add_rounded(slide, x, Inches(2.4), card_w, Inches(3.2), BRAND_LIGHT)
        # 大数字
        add_text_box(slide, x, Inches(2.6), card_w, Inches(1.4), num,
                     size=64, bold=True, color=color, align=PP_ALIGN.CENTER)
        # 描述
        add_text_box(slide, x + Inches(0.3), Inches(4.0), card_w - Inches(0.6), Inches(0.8),
                     desc, size=14, color=BRAND_DARK, align=PP_ALIGN.CENTER)
        # 副标题
        add_text_box(slide, x + Inches(0.3), Inches(4.9), card_w - Inches(0.6), Inches(0.5),
                     sub, size=11, color=BRAND_GRAY, align=PP_ALIGN.CENTER)
    # 引导语
    add_text_box(slide, Inches(0.8), Inches(6.0), Inches(11.5), Inches(0.6),
                 "→  接下来 30 分钟，我告诉你怎么做到。", size=20,
                 bold=True, color=BRAND_BLUE, align=PP_ALIGN.CENTER)
    add_footer(slide)


def make_pain(slide, page_num, total):
    """第 3 页：痛点共鸣（5 大痛点）"""
    set_bg(slide)
    add_header(slide, page_num, total, "2. 痛点共鸣", "5 大真实困境")
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.5),
                 "B2B → A2A：传统打法正在被时代颠覆", size=14, color=BRAND_GRAY)
    # 5 个痛点卡片
    pains = [
        ("01", "战略层", "B2B→A2A\n被时代颠覆", BRAND_RED),
        ("02", "合规层", "产品出门容易\n合规进门太难", BRAND_RED),
        ("03", "数据层", "数据裸奔\n凭感觉拍板", BRAND_RED),
        ("04", "组织层", "招不来/留不住\n用不对", BRAND_RED),
        ("05", "获客层", "展会成本高\n转化难度大", BRAND_RED),
    ]
    card_w = Inches(2.35)
    gap = Inches(0.13)
    start_x = Inches(0.8)
    y = Inches(2.0)
    for i, (num, layer, desc, color) in enumerate(pains):
        x = start_x + (card_w + gap) * i
        # 数字
        add_text_box(slide, x, y, card_w, Inches(0.6), num, size=32, bold=True,
                     color=color, align=PP_ALIGN.CENTER)
        # 层级
        add_text_box(slide, x, y + Inches(0.7), card_w, Inches(0.4), layer,
                     size=14, bold=True, color=BRAND_DARK, align=PP_ALIGN.CENTER)
        # 描述卡片
        add_rounded(slide, x, y + Inches(1.2), card_w, Inches(2.2), BRAND_LIGHT)
        add_text_box(slide, x + Inches(0.15), y + Inches(1.4), card_w - Inches(0.3),
                     Inches(1.9), desc, size=14, color=BRAND_DARK, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)
    # 底部金句
    add_rounded(slide, Inches(0.8), Inches(5.7), Inches(11.5), Inches(1.0), BRAND_RED)
    add_text_box(slide, Inches(0.8), Inches(5.85), Inches(11.5), Inches(0.7),
                 "问题不在您的产品，问题在『数据裸奔』时代。", size=22, bold=True,
                 color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE)
    add_footer(slide)


def make_solution(slide, page_num, total):
    """第 4 页：解决方案"""
    set_bg(slide)
    add_header(slide, page_num, total, "3. 解决方案", "数据大脑 + 重交付")
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.5),
                 "用 AI 把新时代市场规则（数据 / 流量 / AI）交到工厂手里", size=18,
                 bold=True, color=BRAND_BLUE)
    # 4 大模块卡片
    modules = [
        ("数字大脑", "SAG 事件图谱\n+ 行业 Know-How", "解决数据裸奔"),
        ("Bot-Agent 矩阵", "10-50 个数字员工\n7×24 工作", "解决人才稀缺"),
        ("Skills-Map", "企业能力图谱\n动态编排", "解决流程混乱"),
        ("上门陪跑", "数据清洗 + 定制 Skill\n+ 工作流", "解决落地困难"),
    ]
    card_w = Inches(2.8)
    gap = Inches(0.2)
    start_x = Inches(0.8)
    for i, (title, cap, benefit) in enumerate(modules):
        x = start_x + (card_w + gap) * i
        # 卡片
        add_rounded(slide, x, Inches(2.4), card_w, Inches(4.0), BRAND_LIGHT)
        # 顶部色条
        add_rect(slide, x, Inches(2.4), card_w, Inches(0.12), BRAND_BLUE)
        # 标题
        add_text_box(slide, x + Inches(0.2), Inches(2.7), card_w - Inches(0.4), Inches(0.6),
                     title, size=20, bold=True, color=BRAND_DARK, align=PP_ALIGN.CENTER)
        # 能力
        add_text_box(slide, x + Inches(0.2), Inches(3.4), card_w - Inches(0.4), Inches(1.5),
                     cap, size=15, color=BRAND_DARK, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)
        # 解决痛点
        add_text_box(slide, x + Inches(0.2), Inches(5.0), card_w - Inches(0.4), Inches(0.5),
                     benefit, size=13, color=BRAND_GREEN, align=PP_ALIGN.CENTER, bold=True)
    add_footer(slide)


def make_cases(slide, page_num, total):
    """第 5 页：客户证言（3 个案例）"""
    set_bg(slide)
    add_header(slide, page_num, total, "4. 客户证言", "3 个同行成功故事")
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.4),
                 "老板决策 70% 看同行效果", size=14, color=BRAND_GRAY)
    # 3 个案例
    cases = [
        ("客户 A · 机械制造", "年营收 8000 万，主攻欧美", "上 AI 后询盘 +220%、订单 +85%、业务员效率 +50%",
         "30 天搭建，60 天首批询盘", "「AI 把我们的工程师从文员工作里解放出来了」", BRAND_BLUE),
        ("客户 B · 纺织服装", "年营收 1.2 亿，主攻东南亚/中东", "询盘 +180%、转化率 +60%、回本周期 8 个月",
         "30 天搭建，60 天首批询盘", "「以前 3 个业务员做的事，现在 1 个 + AI 就够了」", BRAND_GREEN),
        ("客户 C · 电子电器", "年营收 5000 万，主攻北美", "询盘 +300%、合规问题 -90%、新人 7 天上手",
         "30 天搭建，60 天首批询盘", "「最值钱的是行业 Know-How，AI 真懂我们这行」", BRAND_PURPLE),
    ]
    card_w = Inches(3.95)
    gap = Inches(0.15)
    start_x = Inches(0.8)
    y = Inches(1.85)
    card_h = Inches(5.0)
    for i, (title, bg, result, time, quote, color) in enumerate(cases):
        x = start_x + (card_w + gap) * i
        # 主卡片
        add_rounded(slide, x, y, card_w, card_h, BRAND_LIGHT)
        # 顶部色条
        add_rect(slide, x, y, card_w, Inches(0.12), color)
        # 标题
        add_text_box(slide, x + Inches(0.2), y + Inches(0.25), card_w - Inches(0.4), Inches(0.5),
                     title, size=16, bold=True, color=BRAND_DARK)
        # 背景
        add_text_box(slide, x + Inches(0.2), y + Inches(0.8), card_w - Inches(0.4), Inches(0.4),
                     bg, size=11, color=BRAND_GRAY)
        # 量化结果（大字）
        add_text_box(slide, x + Inches(0.2), y + Inches(1.3), card_w - Inches(0.4), Inches(1.6),
                     result, size=15, bold=True, color=BRAND_GREEN,
                     anchor=MSO_ANCHOR.MIDDLE)
        # 时间
        add_text_box(slide, x + Inches(0.2), y + Inches(3.0), card_w - Inches(0.4), Inches(0.4),
                     f"⏱  {time}", size=11, color=BRAND_BLUE)
        # 客户原话
        add_text_box(slide, x + Inches(0.2), y + Inches(3.6), card_w - Inches(0.4), Inches(1.3),
                     quote, size=12, color=BRAND_DARK)
    add_footer(slide)


def make_advantages(slide, page_num, total):
    """第 6 页：能力优势（5 维壁垒）"""
    set_bg(slide)
    add_header(slide, page_num, total, "5. 能力优势", "五维竞争壁垒")
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.5),
                 "大厂做宽，我们做深；大厂卖工具，我们给结果。", size=20,
                 bold=True, color=BRAND_DARK)
    # 对比表
    headers = ["维度", "大厂 / 通用 AI", "海联智达"]
    rows = [
        ["技术架构", "RAG 单跳匹配", "SAG 多跳推理"],
        ["服务模式", "标准化 SaaS", "重交付陪跑"],
        ["行业深度", "通用语料", "外贸专属大脑"],
        ["效果承诺", "工具上线即结束", "30/60 写进合同"],
        ["数据部署", "平台统一", "独立部署 + 多国"],
    ]
    table_x = Inches(0.8)
    table_y = Inches(2.0)
    table_w = Inches(11.5)
    row_h = Inches(0.7)
    col_w = [Inches(2.3), Inches(4.6), Inches(4.6)]
    # 表头
    x = table_x
    for j, h in enumerate(headers):
        add_rect(slide, x, table_y, col_w[j], row_h,
                 BRAND_DARK if j == 0 else (BRAND_GRAY if j == 1 else BRAND_GREEN))
        align = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
        add_text_box(slide, x + Inches(0.2), table_y, col_w[j] - Inches(0.4), row_h, h,
                     size=15, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), align=align,
                     anchor=MSO_ANCHOR.MIDDLE)
        x += col_w[j]
    # 数据行
    for i, row in enumerate(rows):
        y = table_y + row_h * (i + 1)
        x = table_x
        for j, cell in enumerate(row):
            bg = BRAND_LIGHT if i % 2 == 0 else RGBColor(0xFF, 0xFF, 0xFF)
            add_rect(slide, x, y, col_w[j], row_h, bg)
            color = BRAND_DARK if j != 2 else BRAND_GREEN
            bold = j == 2
            align = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            add_text_box(slide, x + Inches(0.2), y, col_w[j] - Inches(0.4), row_h, cell,
                         size=14, bold=bold, color=color, align=align,
                         anchor=MSO_ANCHOR.MIDDLE)
            x += col_w[j]
    # 底部金句
    add_text_box(slide, Inches(0.8), Inches(6.5), Inches(11.5), Inches(0.4),
                 "—— 我们不只卖软件，而是卖「数据基建 + 组织赋能」", size=14,
                 color=BRAND_GRAY, align=PP_ALIGN.CENTER)
    add_footer(slide)


def make_industries(slide, page_num, total):
    """第 7 页：行业专精（4 行业矩阵）"""
    set_bg(slide)
    add_header(slide, page_num, total, "6. 行业专精", "4 大行业深度 Know-How")
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.5),
                 "我们是为你这一行做的", size=20, bold=True, color=BRAND_DARK)
    industries = [
        ("机械制造", "数控机床、工业配件", "技术规格翻译\nCE/UL/RoHS 合规", BRAND_BLUE),
        ("纺织服装", "面料、辅料、成衣", "流行趋势分析\nBSCI/OEKO-TEX 认证", BRAND_GREEN),
        ("电子电器", "消费电子、IoT", "FCC/CE 认证匹配\n多语言说明书", BRAND_PURPLE),
        ("化工材料", "工业原料、涂料", "MSDS 自动生成\nREACH/危险品合规", BRAND_RED),
    ]
    card_w = Inches(2.85)
    gap = Inches(0.15)
    start_x = Inches(0.8)
    y = Inches(2.2)
    for i, (name, scene, skill, color) in enumerate(industries):
        x = start_x + (card_w + gap) * i
        # 卡片
        add_rounded(slide, x, y, card_w, Inches(3.6), BRAND_LIGHT)
        # 顶部色块（行业名）
        add_rect(slide, x, y, card_w, Inches(0.7), color)
        add_text_box(slide, x, y, card_w, Inches(0.7), name, size=20, bold=True,
                     color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)
        # 场景
        add_text_box(slide, x + Inches(0.2), y + Inches(0.9), card_w - Inches(0.4),
                     Inches(0.5), f"▎  {scene}", size=12, color=BRAND_GRAY)
        # 专属能力
        add_text_box(slide, x + Inches(0.2), y + Inches(1.5), card_w - Inches(0.4),
                     Inches(2.0), "✦ " + skill, size=15, bold=True, color=BRAND_DARK,
                     anchor=MSO_ANCHOR.MIDDLE)
    # 底部
    add_text_box(slide, Inches(0.8), Inches(6.1), Inches(11.5), Inches(0.5),
                 "其他行业可定制（约 60 天）", size=13, color=BRAND_GRAY,
                 align=PP_ALIGN.CENTER)
    add_footer(slide)


def make_pricing(slide, page_num, total):
    """第 8 页：套餐与价格（3 档梯度）"""
    set_bg(slide)
    add_header(slide, page_num, total, "7. 套餐与价格", "3 档梯度升级")
    packages = [
        ("入门版", "¥59,800", "试水期/初创团队", BRAND_BLUE,
         ["数字大脑（自进化）", "Bot-Agent ×10 席", "美国独立网络", "7×24 专属支持", "统一登录/操作追溯"]),
        ("基础版", "¥99,800", "成长期/标准化", BRAND_BLUE,
         ["入门版全部配置", "+ 知识冷启动服务", "+ 5 国服务器可选", "+ Bot-Agent ×25 席", "+ 10 人组织"]),
        ("旗舰版", "¥188,000", "成熟期/深度定制", BRAND_PURPLE,
         ["基础版全部配置", "+ 知识库进阶启动", "+ 定制 Skill + 工作流", "+ 21 国服务器可选", "+ 工程师上门服务"]),
    ]
    card_w = Inches(3.95)
    gap = Inches(0.15)
    start_x = Inches(0.8)
    y = Inches(1.6)
    card_h = Inches(5.3)
    for i, (name, price, target, color, features) in enumerate(packages):
        x = start_x + (card_w + gap) * i
        # 卡片
        add_rounded(slide, x, y, card_w, card_h, BRAND_LIGHT)
        # 顶部色块
        add_rect(slide, x, y, card_w, Inches(1.2), color)
        # 名称
        add_text_box(slide, x, y + Inches(0.1), card_w, Inches(0.5), name,
                     size=22, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
                     align=PP_ALIGN.CENTER)
        # 价格
        add_text_box(slide, x, y + Inches(0.5), card_w, Inches(0.6), price,
                     size=28, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
                     align=PP_ALIGN.CENTER)
        # 目标客户
        add_text_box(slide, x + Inches(0.2), y + Inches(1.3), card_w - Inches(0.4),
                     Inches(0.4), f"▎  {target}", size=12, color=BRAND_GRAY)
        # 功能列表
        feat_y = y + Inches(1.8)
        for feat in features:
            add_text_box(slide, x + Inches(0.3), feat_y, card_w - Inches(0.5), Inches(0.45),
                         f"✓  {feat}", size=13, color=BRAND_DARK)
            feat_y += Inches(0.55)
    add_footer(slide)


def make_guarantee(slide, page_num, total):
    """第 9 页：风险保障（30/60 承诺）"""
    set_bg(slide)
    add_header(slide, page_num, total, "8. 风险保障", "30 天搭建 + 60 天见询盘")
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.5),
                 "白纸黑字写进合同，老板最关心的就是「投错了怎么办」", size=14,
                 color=BRAND_GRAY)
    # 30/60 大字承诺
    add_rounded(slide, Inches(0.8), Inches(1.95), Inches(5.6), Inches(2.5), BRAND_BLUE)
    add_text_box(slide, Inches(0.8), Inches(2.1), Inches(5.6), Inches(1.0), "30",
                 size=80, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(0.8), Inches(3.1), Inches(5.6), Inches(0.5), "天",
                 size=24, color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(0.8), Inches(3.7), Inches(5.6), Inches(0.7),
                 "系统搭建完成", size=20, bold=True,
                 color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    add_rounded(slide, Inches(6.9), Inches(1.95), Inches(5.6), Inches(2.5), BRAND_GREEN)
    add_text_box(slide, Inches(6.9), Inches(2.1), Inches(5.6), Inches(1.0), "60",
                 size=80, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(6.9), Inches(3.1), Inches(5.6), Inches(0.5), "天",
                 size=24, color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(6.9), Inches(3.7), Inches(5.6), Inches(0.7),
                 "首批符合画像的询盘", size=20, bold=True,
                 color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    # 三大保障
    add_text_box(slide, Inches(0.8), Inches(4.7), Inches(11.5), Inches(0.4),
                 "三大保障 · 消除决策阻力", size=18, bold=True, color=BRAND_DARK,
                 align=PP_ALIGN.CENTER)
    guarantees = [
        ("数据安全", "独立部署 + 美国/5国/21国\nTLS 1.3 + AES-256 加密"),
        ("7×24 工程师", "1 小时首次响应\n专属服务群 + 月度复盘"),
        ("效果承诺", "30/60 写进合同\n不达标免费延期至达标"),
    ]
    gw_w = Inches(3.85)
    gw_gap = Inches(0.15)
    gw_start = Inches(0.8)
    gw_y = Inches(5.2)
    for i, (title, desc) in enumerate(guarantees):
        x = gw_start + (gw_w + gw_gap) * i
        add_rounded(slide, x, gw_y, gw_w, Inches(1.5), BRAND_LIGHT)
        add_text_box(slide, x + Inches(0.2), gw_y + Inches(0.15), gw_w - Inches(0.4),
                     Inches(0.5), title, size=16, bold=True, color=BRAND_BLUE)
        add_text_box(slide, x + Inches(0.2), gw_y + Inches(0.7), gw_w - Inches(0.4),
                     Inches(0.7), desc, size=12, color=BRAND_DARK)
    add_footer(slide)


def make_competitor(slide, page_num, total):
    """第 10 页：竞品三体对比"""
    set_bg(slide)
    add_header(slide, page_num, total, "9. 竞品对比", "为什么不是他们")
    add_text_box(slide, Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.5),
                 "老板一定会问：为什么不是阿里/字节/百度做？", size=14,
                 color=BRAND_GRAY)
    headers = ["维度", "海联智达", "通用大厂", "通用 SaaS"]
    rows = [
        ["技术深度", "SAG 多跳推理 + 行业", "通用大模型", "营销自动化"],
        ["行业 Know-How", "机械/纺织/电子/化工", "通用语料", "无行业属性"],
        ["服务模式", "重交付 + 工程师上门", "客户自研", "文档自助"],
        ["数据安全", "独立部署 + 多国服务器", "平台统一", "数据出境风险"],
        ["效果承诺", "30/60 写进合同", "工具上线即结束", "工具上线即结束"],
        ["客户成本", "中（¥6-18 万/年）", "高（百万+）", "中高（年费+实施）"],
    ]
    table_x = Inches(0.8)
    table_y = Inches(2.0)
    row_h = Inches(0.62)
    col_w = [Inches(2.0), Inches(3.4), Inches(3.1), Inches(3.0)]
    # 表头
    x = table_x
    for j, h in enumerate(headers):
        color = BRAND_GREEN if j == 1 else BRAND_DARK
        add_rect(slide, x, table_y, col_w[j], row_h, color)
        add_text_box(slide, x + Inches(0.15), table_y, col_w[j] - Inches(0.3), row_h, h,
                     size=14, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += col_w[j]
    # 数据行
    for i, row in enumerate(rows):
        y = table_y + row_h * (i + 1)
        x = table_x
        for j, cell in enumerate(row):
            bg = BRAND_LIGHT if i % 2 == 0 else RGBColor(0xFF, 0xFF, 0xFF)
            add_rect(slide, x, y, col_w[j], row_h, bg)
            color = BRAND_GREEN if j == 1 else BRAND_DARK
            bold = j == 1
            add_text_box(slide, x + Inches(0.15), y, col_w[j] - Inches(0.3), row_h, cell,
                         size=12, bold=bold, color=color,
                         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            x += col_w[j]
    add_footer(slide)


def make_cta(slide, page_num, total):
    """第 11 页：行动号召"""
    set_bg(slide, BRAND_DARK)
    # 主标题
    add_text_box(slide, Inches(0.8), Inches(1.0), Inches(11.5), Inches(0.7),
                 "现在该做什么", size=18, color=BRAND_GREEN)
    add_text_box(slide, Inches(0.8), Inches(1.6), Inches(11.5), Inches(1.5),
                 "从「数据裸奔」到「数据大脑」", size=44, bold=True,
                 color=RGBColor(0xFF, 0xFF, 0xFF))
    add_text_box(slide, Inches(0.8), Inches(2.8), Inches(11.5), Inches(0.8),
                 "只差一个决策的距离。", size=32, bold=True, color=BRAND_BLUE)
    # 3 步行动
    add_text_box(slide, Inches(0.8), Inches(4.0), Inches(11.5), Inches(0.5),
                 "三步行动 · 今天就可以启动", size=16, color=BRAND_GREEN)
    steps = [
        ("① 决策路径", "选入门版（¥59,800）\n跑通 30/60 承诺", "今天"),
        ("② 数据准备", "业务访谈 + 历史数据整理\n（销售配合）", "1-2 周"),
        ("③ 上线运营", "30 天系统搭建\n60 天首批询盘", "60 天"),
    ]
    sw = Inches(3.85)
    sg = Inches(0.15)
    sx = Inches(0.8)
    sy = Inches(4.5)
    for i, (title, desc, time) in enumerate(steps):
        x = sx + (sw + sg) * i
        add_rounded(slide, x, sy, sw, Inches(1.8), BRAND_BLUE)
        add_text_box(slide, x + Inches(0.3), sy + Inches(0.15), sw - Inches(0.6), Inches(0.5),
                     title, size=18, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        add_text_box(slide, x + Inches(0.3), sy + Inches(0.7), sw - Inches(0.6), Inches(0.7),
                     desc, size=12, color=RGBColor(0xCC, 0xD0, 0xD6))
        add_text_box(slide, x + Inches(0.3), sy + Inches(1.4), sw - Inches(0.6), Inches(0.3),
                     f"⏱  {time}", size=11, color=BRAND_GREEN, bold=True)
    # 紧迫感
    add_text_box(slide, Inches(0.8), Inches(6.5), Inches(11.5), Inches(0.4),
                 "⚡  限时权益：早鸟签约送 ¥20,000 冷启动服务  |  14 天免费 PoC",
                 size=14, color=BRAND_GOLD, align=PP_ALIGN.CENTER)


def make_qa(slide, page_num, total):
    """第 12 页：Q&A 弹药库"""
    set_bg(slide)
    add_header(slide, page_num, total, "10. Q&A 弹药库", "老板最常问的 15 个问题")
    qa_pairs = [
        ("Q1：和阿里有什么区别？", "阿里是流量平台（获客），我们是数据大脑（接住+转化）。两者不冲突，可叠加。"),
        ("Q2：多久能见到效果？", "30 天系统上线、60 天首批询盘——写入合同。"),
        ("Q3：效果不达标怎么办？", "30/60 写进合同，达不到免费延期至达标。"),
        ("Q4：数据安全吗？", "独立部署 + 美国/5国/21国可选 + TLS 1.3 + AES-256 加密。"),
        ("Q5：能试用吗？", "14 天免费 PoC（需审核），风险我们承担。"),
        ("Q6：员工不会用？", "3 阶段培训 + 7×24 工程师答疑 + 新人 7 天上手。"),
        ("Q7：行业能用吗？", "机械/纺织/电子/化工 4 大行业专精，其他可定制。"),
    ]
    # 左侧
    y = Inches(1.4)
    for i in range(0, 4):
        if i >= len(qa_pairs):
            break
        q, a = qa_pairs[i]
        add_rounded(slide, Inches(0.4), y, Inches(6.3), Inches(1.2), BRAND_LIGHT)
        add_text_box(slide, Inches(0.6), y + Inches(0.1), Inches(6.0), Inches(0.4),
                     q, size=12, bold=True, color=BRAND_BLUE)
        add_text_box(slide, Inches(0.6), y + Inches(0.5), Inches(6.0), Inches(0.7),
                     "A: " + a, size=11, color=BRAND_DARK)
        y += Inches(1.32)
    # 右侧
    y = Inches(1.4)
    for i in range(4, 8):
        if i >= len(qa_pairs):
            break
        q, a = qa_pairs[i]
        add_rounded(slide, Inches(6.85), y, Inches(6.3), Inches(1.2), BRAND_LIGHT)
        add_text_box(slide, Inches(7.05), y + Inches(0.1), Inches(6.0), Inches(0.4),
                     q, size=12, bold=True, color=BRAND_BLUE)
        add_text_box(slide, Inches(7.05), y + Inches(0.5), Inches(6.0), Inches(0.7),
                     "A: " + a, size=11, color=BRAND_DARK)
        y += Inches(1.32)
    # 完整 Q&A 提示
    add_text_box(slide, Inches(0.4), Inches(6.8), Inches(12.5), Inches(0.4),
                 "📖  完整 15 个 Q&A 详见销售手册（含价格、定制、合规、合同等）",
                 size=12, color=BRAND_GRAY, align=PP_ALIGN.CENTER)
    add_footer(slide)


# ========== 主流程 ==========
def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    total = 12
    builders = [
        make_cover,      # 1
        make_hook,       # 2
        make_pain,       # 3
        make_solution,   # 4
        make_cases,      # 5
        make_advantages, # 6
        make_industries, # 7
        make_pricing,    # 8
        make_guarantee,  # 9
        make_competitor, # 10
        make_cta,        # 11
        make_qa,         # 12
    ]
    for i, fn in enumerate(builders):
        slide = prs.slides.add_slide(blank)
        fn(slide, i + 1, total)
        print(f"  [OK] Slide {i+1}/{total} - {fn.__name__}")

    output = "D:/MCP_SERVER/HLZD-SALES/海联智达-外贸AI赋能方案-v3.pptx"
    prs.save(output)
    print(f"\n[SUCCESS] PPT generated: {output}")
    print(f"   Total slides: {total}")
    print(f"   Format: 16:9 widescreen (1920x1080)")


if __name__ == "__main__":
    main()
