# -*- coding: utf-8 -*-
"""
外泌体报价分析报告 HTML 生成器
"""
import os

products = [
    {'name': '肺部雾化制剂', 'spec': '冲气/雾化吸入<br>200亿颗粒<br>5ml/支 × 2支', 'tiers': [
        {'qty': '≤500 份', 'price': 160, 'logistics': 140, 'intl': '1200-2000'},
        {'qty': '500-1000 份', 'price': 150, 'logistics': 140, 'intl': None},
        {'qty': '>1000 份', 'price': 135, 'logistics': 140, 'intl': None}],
     'shipping_mode': '常温', 'features': '呼吸道肺部修护、气道舒缓养护'},
    {'name': '面部修复制剂', 'spec': '微明/善利<br>500亿颗粒<br>+ 200亿颗粒', 'tiers': [
        {'qty': '≤500 份', 'price': 350, 'logistics': 200, 'intl': '2200-4000'},
        {'qty': '≤1000 份', 'price': 320, 'logistics': 200, 'intl': None},
        {'qty': '>1000 份', 'price': 290, 'logistics': 200, 'intl': None}],
     'shipping_mode': '冷链', 'features': '肌肤屏障修护、适配水光/微针'},
    {'name': '眼部润养制剂', 'spec': '见明·次抛眼笔<br>200亿颗粒<br>5ml/支 × 2支', 'tiers': [
        {'qty': '≤500 份', 'price': 170, 'logistics': 140, 'intl': '1200-2000'},
        {'qty': '500-1000 份', 'price': 160, 'logistics': 140, 'intl': None},
        {'qty': '>1000 份', 'price': 145, 'logistics': 140, 'intl': None}],
     'shipping_mode': '常温', 'features': '眼底干涩舒缓、日常眼部抗衰润护'},
    {'name': '全身系统制剂', 'spec': '周行·系统递送<br>2000亿颗粒<br>冻干粉/冷链液', 'tiers': [
        {'qty': '≤500 份', 'price': 700, 'logistics': 70, 'intl': '3600-5800'},
        {'qty': '≤1000 份', 'price': 650, 'logistics': 70, 'intl': None},
        {'qty': '>1000 份', 'price': 550, 'logistics': 70, 'intl': None}],
     'shipping_mode': '冷链', 'features': '全身细胞抗衰、内源机能调节'},
    {'name': '口服/舌下制剂', 'spec': '含德·舌下透膜<br>速溶冻干片', 'tiers': [
        {'qty': '≤500 份', 'price': 70, 'logistics': 20, 'intl': '300-700'},
        {'qty': '≤1000 份', 'price': 60, 'logistics': 20, 'intl': None},
        {'qty': '>1000 份', 'price': 48, 'logistics': 20, 'intl': None}],
     'shipping_mode': '常温（片剂）', 'features': '舌下速溶直达循环、亚健康保养'},
]

def card_html(p, idx):
    tiers_html = ''
    for t in p['tiers']:
        intl_html = '<span class="intl-tag">🌍 国际价 ' + str(t["intl"]) + '</span>' if t['intl'] else ''
        tiers_html += '<div class="tier-row"><span class="qty">' + t["qty"] + '</span><span class="price">¥' + str(t["price"]) + '</span><span class="logistics">+¥' + str(t["logistics"]) + '/份 物流</span><span class="intl">' + intl_html + '</span></div>'

    first = p['tiers'][0]['price']
    last = p['tiers'][-1]['price']
    discount = round((1 - last / first) * 100, 1)
    log_ratio = round((p['tiers'][0]['logistics'] / first) * 100, 1)
    log_color = '#ef4444' if log_ratio > 30 else ('#f59e0b' if log_ratio > 20 else '#10b981')

    return (
        '<div class="product-card">'
        '<div class="card-header">'
        '<div class="card-num">' + str(idx + 1) + '</div>'
        '<div><h3>' + p["name"] + '</h3>'
        '<div class="card-spec">' + p["spec"] + '</div></div></div>'
        '<div class="card-body">'
        '<div class="meta-grid">'
        '<div class="meta-item"><div class="meta-label">应用场景</div><div class="meta-value">' + p["features"] + '</div></div>'
        '<div class="meta-item"><div class="meta-label">运输方式</div><div class="meta-value shipping-badge">' + p["shipping_mode"] + '</div></div>'
        '<div class="meta-item"><div class="meta-label">阶梯折扣</div><div class="meta-value"><span class="discount">-' + str(discount) + '%</span></div></div>'
        '<div class="meta-item"><div class="meta-label">物流费占比</div><div class="meta-value" style="color:' + log_color + '"><strong>' + str(log_ratio) + '%</strong></div></div>'
        '</div>'
        '<div class="tier-table">'
        '<div class="tier-header"><span>采购量</span><span>单价</span><span>物流费</span></div>'
        + tiers_html +
        '</div></div></div>'
    )

products_html = ''.join([card_html(p, i) for i, p in enumerate(products)])

# 对比表行
compare_rows = ''
for p in products:
    first = p['tiers'][0]['price']
    last = p['tiers'][-1]['price']
    discount = round((1 - last / first) * 100, 1)
    log_ratio = round((p['tiers'][0]['logistics'] / first) * 100, 1)
    log_color = '#ef4444' if log_ratio > 30 else ('#f59e0b' if log_ratio > 20 else '#10b981')
    discount_color = '#ef4444' if discount > 25 else ('#f59e0b' if discount > 18 else '#10b981')
    intl_val = p['tiers'][0]['intl'] if p['tiers'][0]['intl'] else '—'
    compare_rows += (
        '<tr>'
        '<td><strong>' + p["name"] + '</strong></td>'
        '<td class="text-center">' + p["shipping_mode"] + '</td>'
        '<td class="text-right">¥' + str(first) + ' - ' + str(last) + '</td>'
        '<td class="text-center"><span class="badge" style="background:' + discount_color + '20;color:' + discount_color + '">-' + str(discount) + '%</span></td>'
        '<td class="text-center"><span class="badge" style="background:' + log_color + '20;color:' + log_color + '">' + str(log_ratio) + '%</span></td>'
        '<td class="text-center">' + intl_val + '</td>'
        '</tr>'
    )

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>外泌体产品报价分析报告</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
:root {
  --primary: #1F6FEB;
  --primary-dark: #0A1F44;
  --accent: #10B981;
  --warning: #F59E0B;
  --danger: #EF4444;
  --bg: #F8FAFC;
  --card: #FFFFFF;
  --border: #E2E8F0;
  --text: #1E293B;
  --text-muted: #64748B;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}
.hero {
  background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
  color: white;
  padding: 4rem 2rem 3rem;
  text-align: center;
}
.hero h1 { font-size: 2.5rem; margin: 0 0 0.5rem; font-weight: 700; }
.hero p { font-size: 1rem; opacity: 0.9; margin: 0; }
.hero .meta { margin-top: 1.5rem; display: inline-flex; gap: 2rem; font-size: 0.875rem; opacity: 0.8; flex-wrap: wrap; justify-content: center; }
.container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
.section { background: var(--card); border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.section-title { display: flex; align-items: center; gap: 0.75rem; margin: 0 0 1.5rem; font-size: 1.5rem; font-weight: 700; color: var(--primary-dark); }
.section-title .num { background: var(--primary); color: white; width: 2rem; height: 2rem; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 1rem; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
.kpi { background: linear-gradient(135deg, #fff 0%, #f8fafc 100%); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; text-align: center; }
.kpi-label { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 0.5rem; }
.kpi-value { font-size: 2rem; font-weight: 700; color: var(--primary-dark); }
.kpi-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }
.product-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1rem; }
.product-card { background: white; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; transition: all 0.2s; }
.product-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
.card-header { padding: 1rem; background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); color: white; display: flex; gap: 0.75rem; align-items: center; }
.card-num { background: rgba(255,255,255,0.2); width: 2rem; height: 2rem; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; }
.card-header h3 { margin: 0; font-size: 1.125rem; }
.card-spec { font-size: 0.75rem; opacity: 0.85; margin-top: 0.25rem; }
.card-body { padding: 1rem; }
.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px dashed var(--border); }
.meta-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem; }
.meta-value { font-size: 0.875rem; font-weight: 500; }
.shipping-badge { background: #e0f2fe; color: #075985; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; display: inline-block; }
.tier-table { font-size: 0.875rem; }
.tier-header, .tier-row { display: grid; grid-template-columns: 1.5fr 1fr 1.5fr 1.5fr; padding: 0.5rem 0.25rem; align-items: center; gap: 0.5rem; }
.tier-header { background: var(--bg); border-radius: 4px; color: var(--text-muted); font-weight: 500; font-size: 0.75rem; }
.tier-row { background: linear-gradient(90deg, transparent 0%, #f8fafc 100%); margin: 0.25rem 0; border-radius: 4px; }
.tier-row .price { font-weight: 700; color: var(--primary-dark); font-size: 1rem; }
.tier-row .logistics { color: var(--text-muted); font-size: 0.75rem; }
.intl-tag { background: #fef3c7; color: #92400e; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; white-space: nowrap; }
.compare-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.compare-table th { background: var(--bg); padding: 0.75rem; text-align: left; font-weight: 600; color: var(--text-muted); border-bottom: 1px solid var(--border); }
.compare-table td { padding: 0.875rem 0.75rem; border-bottom: 1px solid var(--border); }
.compare-table tr:hover { background: var(--bg); }
.text-right { text-align: right; }
.text-center { text-align: center; }
.badge { display: inline-block; padding: 0.25rem 0.625rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1rem; }
.chart-card { background: white; border: 1px solid var(--border); border-radius: 10px; padding: 1rem; }
.chart-title { font-size: 1rem; font-weight: 600; margin: 0 0 1rem; color: var(--text); }
.chart { height: 320px; }
.alert-grid { display: grid; gap: 0.75rem; }
.alert { padding: 1rem; border-radius: 8px; display: flex; gap: 1rem; align-items: flex-start; }
.alert-icon { font-size: 1.5rem; flex-shrink: 0; }
.alert-body { flex: 1; }
.alert-title { font-weight: 600; margin-bottom: 0.25rem; }
.alert-desc { font-size: 0.875rem; opacity: 0.85; }
.alert-critical { background: #fef2f2; border-left: 4px solid var(--danger); }
.alert-warning { background: #fffbeb; border-left: 4px solid var(--warning); }
.alert-success { background: #f0fdf4; border-left: 4px solid var(--accent); }
.alert-info { background: #eff6ff; border-left: 4px solid var(--primary); }
.alert ul { margin-top: 0.5rem; padding-left: 1.5rem; }
.recommendation { background: linear-gradient(135deg, var(--primary-dark), var(--primary)); color: white; border-radius: 12px; padding: 2rem; }
.recommendation h2 { margin: 0 0 1rem; color: white; }
.recommendation-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
.rec-card { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 8px; padding: 1rem; }
.rec-num { font-size: 0.75rem; opacity: 0.7; letter-spacing: 0.1em; }
.rec-title { font-weight: 600; margin: 0.5rem 0; }
.rec-desc { font-size: 0.875rem; opacity: 0.9; }
.footer { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.875rem; }
@media (max-width: 768px) {
  .hero { padding: 3rem 1rem 2rem; }
  .hero h1 { font-size: 1.75rem; }
  .container { padding: 1rem; }
  .product-grid { grid-template-columns: 1fr; }
  .chart-grid { grid-template-columns: 1fr; }
  .tier-header, .tier-row { grid-template-columns: 1fr 1fr; }
  .tier-row .logistics, .tier-row .intl { grid-column: span 2; }
}
</style>
</head>
<body>

<div class="hero">
  <h1>📊 外泌体产品报价分析报告</h1>
  <p>Exosome Products Quote Analysis · 出口贸易版</p>
  <div class="meta">
    <span>📅 2026-07-07</span>
    <span>📦 5 类产品</span>
    <span>🌍 出口资质已确认</span>
  </div>
</div>

<div class="container">

  <div class="section">
    <h2 class="section-title"><span class="num">1</span>核心指标</h2>
    <div class="kpi-grid">
      <div class="kpi">
        <div class="kpi-label">产品类别</div>
        <div class="kpi-value">5</div>
        <div class="kpi-sub">个品类</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">价格区间</div>
        <div class="kpi-value">¥48-700</div>
        <div class="kpi-sub">最低 → 最高</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">最大折扣</div>
        <div class="kpi-value" style="color: var(--warning)">31%</div>
        <div class="kpi-sub">口服/舌下制剂</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">物流费占比</div>
        <div class="kpi-value" style="color: var(--danger)">57%</div>
        <div class="kpi-sub">面部修复 · 异常高</div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title"><span class="num">2</span>产品详情与定价</h2>
    <div class="product-grid">
      ''' + products_html + '''
    </div>
  </div>

  <div class="section">
    <h2 class="section-title"><span class="num">3</span>横向对比矩阵</h2>
    <div style="overflow-x: auto;">
    <table class="compare-table">
      <thead>
        <tr>
          <th>产品</th>
          <th class="text-center">运输方式</th>
          <th class="text-right">价格区间（¥）</th>
          <th class="text-center">阶梯折扣</th>
          <th class="text-center">物流占比</th>
          <th class="text-center">国际参考</th>
        </tr>
      </thead>
      <tbody>
        ''' + compare_rows + '''
      </tbody>
    </table>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title"><span class="num">4</span>数据可视化</h2>
    <div class="chart-grid">
      <div class="chart-card">
        <h3 class="chart-title">📈 阶梯价格走势</h3>
        <div id="chart-price" class="chart"></div>
      </div>
      <div class="chart-card">
        <h3 class="chart-title">🎯 物流费占比（低于 20% 为正常）</h3>
        <div id="chart-log" class="chart"></div>
      </div>
      <div class="chart-card">
        <h3 class="chart-title">🌍 国内 vs 国际价对比</h3>
        <div id="chart-intl" class="chart"></div>
      </div>
      <div class="chart-card">
        <h3 class="chart-title">💰 批量折扣力度</h3>
        <div id="chart-discount" class="chart"></div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title"><span class="num">5</span>⚠️ 核心疑问（需澄清）</h2>
    <div class="alert-grid">
      <div class="alert alert-critical">
        <div class="alert-icon">🔴</div>
        <div class="alert-body">
          <div class="alert-title">1. 物流费占比严重失衡</div>
          <div class="alert-desc">面部修复制剂物流费 200/份（占 57%），但同类常温运输产品仅 140/份甚至 70/份。同时，"冷链"的全身系统制剂物流费仅 70/份，"常温"的面部修复反而 200/份——明显逻辑矛盾。<strong>建议：要求按"冷链 / 常温 / 冷媒填充"分类重新报价。</strong></div>
        </div>
      </div>

      <div class="alert alert-critical">
        <div class="alert-icon">🔴</div>
        <div class="alert-body">
          <div class="alert-title">2. 国际参考价缺乏可追溯性</div>
          <div class="alert-desc">所有"国际价"仅给区间，未注明：<strong>品牌、地区、采购渠道、参考日期、币种、是否含税</strong>。国外生物制剂终端价差异极大（如诊所 vs DTC 电商相差 5 倍），无参照系的价格对比无意义。<strong>建议：要求附 3 份以上竞品报价单或链接。</strong></div>
        </div>
      </div>

      <div class="alert alert-warning">
        <div class="alert-icon">🟡</div>
        <div class="alert-body">
          <div class="alert-title">3. 阶梯折扣"反常识"</div>
          <div class="alert-desc">低单价产品（口服 70 元）折扣力度 31% 远超系统制剂 21%。常规定价中，高单价产品折扣空间更大。建议核查阶梯划分逻辑。</div>
        </div>
      </div>

      <div class="alert alert-warning">
        <div class="alert-icon">🟡</div>
        <div class="alert-body">
          <div class="alert-title">4. "份"作为计量单位模糊</div>
          <div class="alert-desc">所有产品都以"份"计量，但不同产品的"份"组成差异很大（面部修复 1 份含 3 支 + 配件；眼部 1 份 = 眼笔 2 支；肺部 1 份摊销雾化器）。<strong>建议：明确每份的内容物清单。</strong></div>
        </div>
      </div>

      <div class="alert alert-warning">
        <div class="alert-icon">🟡</div>
        <div class="alert-body">
          <div class="alert-title">5. 规格标准化不足</div>
          <div class="alert-desc">"200 亿颗粒" / "500 亿颗粒" 等口径需注明：颗粒定义（NTA 计数？流式？蛋白总量？）、批次稳定性数据、出厂活率指标。<strong>对于生物制品，含量质检报告是出口必备。</strong></div>
        </div>
      </div>

      <div class="alert alert-warning">
        <div class="alert-icon">🟡</div>
        <div class="alert-body">
          <div class="alert-title">6. 报关成本"按份固定"</div>
          <div class="alert-desc">报关+国际物流按"140/份或 200/份"固定收费，未区分：目的国、批量、是否需特殊检疫（生物制品出口常需冷链检疫证明）。建议按目的国和批量阶梯报价。</div>
        </div>
      </div>

      <div class="alert alert-info">
        <div class="alert-icon">🔵</div>
        <div class="alert-body">
          <div class="alert-title">7. 缺失的关键商务条款</div>
          <div class="alert-desc">
            ❌ 报价有效期　❌ 付款条件（定金/尾款比例）　❌ 交货周期（FOB / CIF）<br>
            ❌ 最小起订量（MOQ）　❌ 质保期与退换货政策　❌ 关税与目的地清关责任<br>
            <strong>建议：补全商务条款后再签约。</strong>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="section" style="background: transparent; padding: 0;">
    <div class="recommendation">
      <h2>🎯 行动建议</h2>
      <div class="recommendation-grid">
        <div class="rec-card">
          <div class="rec-num">P0 · 即刻</div>
          <div class="rec-title">核实物流明细</div>
          <div class="rec-desc">要求按"冷链/常温/特殊处理"分类重新拆分报价，明确每个产品的真实运输成本结构。</div>
        </div>
        <div class="rec-card">
          <div class="rec-num">P0 · 即刻</div>
          <div class="rec-title">索取国际报价凭证</div>
          <div class="rec-desc">要求提供 3 份以上国际竞品报价单（注明品牌、地区、日期、币种、是否含税），作为议价参照系。</div>
        </div>
        <div class="rec-card">
          <div class="rec-num">P1 · 重要</div>
          <div class="rec-title">补全商务条款</div>
          <div class="rec-desc">报价有效期、付款方式、交货周期、MOQ、质保期、退换货政策、关税责任划分——缺一不可。</div>
        </div>
        <div class="rec-card">
          <div class="rec-num">P1 · 重要</div>
          <div class="rec-title">规格标准化</div>
          <div class="rec-desc">明确"颗粒"定义（NTA/流式）、批次质检报告、出厂活率指标——这是出口生物制品的硬性要求。</div>
        </div>
        <div class="rec-card">
          <div class="rec-num">P2 · 建议</div>
          <div class="rec-title">阶梯折扣复核</div>
          <div class="rec-desc">口服舌下 31% 折扣异常，请报价方解释定价逻辑，避免后续议价时被抓住把柄。</div>
        </div>
        <div class="rec-card">
          <div class="rec-num">P2 · 建议</div>
          <div class="rec-title">每份内容物清单</div>
          <div class="rec-desc">明确每份包含哪些具体物料（支数、配件、赠品），避免"份"作为模糊计量单位导致后续争议。</div>
        </div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title"><span class="num">6</span>✅ 出口资质说明</h2>
    <div class="alert alert-success">
      <div class="alert-icon">🌍</div>
      <div class="alert-body">
        <div class="alert-title">已确认资质（用户提供）</div>
        <div class="alert-desc">
          本报告基于"<strong>供方已具备出口资质</strong>"前提撰写，未涉及合规性追问。但仍建议出口合同中明确以下文件：
          <ul>
            <li>HS Code（生物制剂常见 3002、3004 等）</li>
            <li>原产地证明（CO）</li>
            <li>出口药品/生物制品备案表</li>
            <li>冷链运输温度记录</li>
            <li>目的国进口许可（如需）</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <div class="footer">
    <p>📊 外泌体报价分析报告 · 由海联智达 HLZD 战略分析团队生成</p>
    <p>2026-07-07 · 仅供业务参考，不构成投资建议</p>
  </div>

</div>

<script>
const priceChart = echarts.init(document.getElementById('chart-price'));
priceChart.setOption({
  tooltip: { trigger: 'axis' },
  legend: { data: ['≤500', '500-1000', '>1000'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['肺部雾化','面部修复','眼部润养','全身系统','口服舌下'] },
  yAxis: { type: 'value', name: '元/份' },
  series: [
    { name: '≤500', type: 'bar', data: [160, 350, 170, 700, 70], itemStyle: { color: '#1F6FEB' }},
    { name: '500-1000', type: 'bar', data: [150, 320, 160, 650, 60], itemStyle: { color: '#10B981' }},
    { name: '>1000', type: 'bar', data: [135, 290, 145, 550, 48], itemStyle: { color: '#F59E0B' }}
  ]
});

const logChart = echarts.init(document.getElementById('chart-log'));
logChart.setOption({
  tooltip: { trigger: 'axis', formatter: '{b}<br/>物流占比: {c}%' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['面部修复', '口服舌下', '眼部润养', '全身系统', '肺部雾化'] },
  yAxis: { type: 'value', name: '占单价 (%)' },
  series: [{
    type: 'bar',
    data: [
      { value: 57.1, itemStyle: { color: '#EF4444' }},
      { value: 28.6, itemStyle: { color: '#F59E0B' }},
      { value: 82.4, itemStyle: { color: '#1F6FEB' }},
      { value: 10, itemStyle: { color: '#10B981' }},
      { value: 87.5, itemStyle: { color: '#1F6FEB' }}
    ],
    label: { show: true, position: 'top', formatter: '{c}%' },
    markLine: { silent: true, data: [{ yAxis: 20, label: { formatter: '正常阈值 20%', color: '#10B981' }, lineStyle: { color: '#10B981' }}] }
  }]
});

const intlChart = echarts.init(document.getElementById('chart-intl'));
intlChart.setOption({
  tooltip: { trigger: 'axis' },
  legend: { data: ['国内报价', '国际低价', '国际高价'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['肺部雾化','面部修复','眼部润养','全身系统','口服舌下'] },
  yAxis: { type: 'value', name: '元' },
  series: [
    { name: '国内报价', type: 'bar', data: [160, 350, 170, 700, 70], itemStyle: { color: '#1F6FEB' }},
    { name: '国际低价', type: 'bar', data: [1200, 2200, 1200, 3600, 300], itemStyle: { color: '#94a3b8' }},
    { name: '国际高价', type: 'bar', data: [2000, 4000, 2000, 5800, 700], itemStyle: { color: '#64748b' }}
  ]
});

const discChart = echarts.init(document.getElementById('chart-discount'));
discChart.setOption({
  tooltip: { trigger: 'axis', formatter: '{b}<br/>折扣: {c}%' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['口服舌下','全身系统','面部修复','肺部雾化','眼部润养'] },
  yAxis: { type: 'value', name: '折扣 (%)' },
  series: [{
    type: 'line',
    data: [31.4, 21.4, 17.1, 15.6, 14.7],
    smooth: true,
    lineStyle: { color: '#1F6FEB', width: 3 },
    itemStyle: { color: '#F59E0B' },
    areaStyle: { color: 'rgba(31,111,235,0.2)' },
    label: { show: true, formatter: '{c}%' }
  }]
});

window.addEventListener('resize', function() {
  priceChart.resize();
  logChart.resize();
  intlChart.resize();
  discChart.resize();
});
</script>

</body>
</html>'''

out_path = r'C:\Users\13864\Desktop\外泌体报价分析报告.html'
if os.path.exists(out_path):
    os.remove(out_path)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[OK] {out_path}")
print(f"    Size: {os.path.getsize(out_path)/1024:.1f} KB")
