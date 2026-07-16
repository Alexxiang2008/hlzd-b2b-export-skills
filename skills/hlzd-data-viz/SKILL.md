---
name: hlzd-data-viz
description: "B2B 销售数据交互式可视化 —— 销售漏斗 / 询盘分析看板 / 客户地理分布地图 / 通用 D3 图表（柱/折/饼/热力/散点/弦图/力导向）。D3.js v7 CDN，输出自包含 HTML。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: analytics
  triggered_by:
    - 销售漏斗
    - 询盘分析
    - 转化漏斗
    - 客户地理分布
    - 地图可视化
    - 数据看板
    - 看板
    - dashboard
    - 漏斗图
    - D3 图表
    - 交互式图表
    - 折线图
    - 柱状图
    - 热力图
    - 饼图
    - 网络图
    - 散点图
    - 弦图
    - 力导向图
    - 询盘看板
    - data viz
    - sales funnel
    - interactive chart
    - dashboard
---

# hlzd-d3-viz — B2B 数据可视化

> 解决 B2B 数据洞察问题：销售漏斗 + 询盘看板 + 客户地理，3 大 HLZD 场景即开即用。

---

## Quick Commands

```bash
# 销售漏斗图（HLZD 特色）
hlzd-d3-viz funnel --source hlzd_b2b --period month --lang zh_CN

# 询盘分析看板（6 图组合）
hlzd-d3-viz dashboard --source hlzd_b2b --time-range month

# 客户地理分布（世界地图 + 气泡）
hlzd-d3-viz geo --source hlzd_b2b --region world

# 通用图表（柱状/折线/饼图/热力等）
hlzd-d3-viz bar --data-file data.csv --x category --y value
hlzd-d3-viz line --data-file data.csv --x date --y count
hlzd-d3-viz pie --data-file data.csv --label type --value count

# 用户 JSON 自定义数据
hlzd-d3-viz funnel --source user_json --data-file my_data.json

# 用户 CSV
hlzd-d3-viz dashboard --source csv --data-file inquiries.csv

# CLI 底层调用
py scripts/orchestrator.py --chart-type funnel --source hlzd_b2b --lang zh_CN
```

---

## 定位

| 对比项 | Chart.js / ECharts | **hlzd-d3-viz** |
|---|---|---|
| 图表类型 | 标准库 | **标准 + HLZD 三大场景**（漏斗/看板/地理）|
| 定制能力 | 模板化（受限于库）| **完全可控**（D3 直接操作 SVG）|
| 数据源 | 静态 JSON | **HLZD-B2B工业品调研 闭环**（自动检测最新）|
| 品牌色 | 库默认 | **HLZD 品牌色统一** |
| 协同能力 | 独立 | **HLZD skills 体系一员**（与办公/图片/视频联动）|
| 输出格式 | HTML 片段 | **自包含 HTML**（含 D3.js CDN）|

**核心原则**：B2B 数据可视化不是"画图"，是"洞察 + 决策"。

---

## 核心能力矩阵

| 能力 | 实现 | 适用场景 | 来源 |
|---|---|---|---|
| **销售漏斗图** | funnel.js（SVG path 拼接）| 询盘→报价→谈判→成交 转化率 | ⭐ HLZD 特色 |
| **询盘分析看板** | dashboard-quote.js（6 图组合）| 销售汇报/周报/月报 | ⭐ HLZD 特色 |
| **客户地理分布** | geo-customers.js（d3-geo + TopoJSON）| 市场分布/区域分析 | ⭐ HLZD 特色 |
| 柱状图 | bar.js | 类别对比 | 通用 |
| 折线图 | line.js | 趋势分析 | 通用 |
| 饼图 | pie.js | 占比分析 | 通用 |
| 热力图 | heatmap.js | 矩阵/交叉分析 | 通用 |
| 散点图 | scatter.js | 相关性分析（询盘 vs 成交率）| 通用 v0.2 |
| 弦图 | chord.js | 关系网络（客户-产品关系）| 通用 v0.2 |
| 力导向图 | force-directed.js | 复杂网络（客户-供应商-产品）| 通用 v0.2 |

---

## 数据源

| 数据源 | 用途 | 备注 |
|---|---|---|
| HLZD-B2B工业品调研 | 询盘/客户/市场数据 | 主要数据源，闭环调用 |
| hlzd-image-gen | 嵌入图（产品/场景）| dashboard 中插入图片 |
| 用户 JSON | 自定义数据 | data_loader.load_from_json |
| 用户 CSV | 表格数据 | data_loader.load_from_csv |
| Demo 数据 | 无数据时用 | data_loader.generate_demo_data |

---

## 工作流（主流程）

```
输入（chart_type + 数据源 + 可选时间范围/区域）
    ↓
[1] NLU 解析（Claude 自身）
    → 实体抽取（chart_type/data_source/time_range/region/language）
    → 追问缺失字段
    ↓
[2] B2B 闭环检测（可选）
    → 扫描 HLZD-B2B工业品调研 目录
    → 按 mtime 取最新报告 → 解析 markdown 补全实体
    ↓
[3] 展示理解回执（Markdown 表格）
    ↓
[4] 数据接入 + 校验
    → 从数据源加载（HLZD-B2B / JSON / CSV / Demo）
    → 字段非空 + 类型正确
    ↓
[5] 图表路由 + 渲染
    ├─ 漏斗 → funnel.js
    ├─ 看板 → dashboard-quote.js
    ├─ 地理 → geo-customers.js
    └─ 通用 → bar/line/pie/heatmap/...
    ↓
[6] HTML 输出
    → Jinja2 模板 + D3.js CDN（自包含）
    → outputs/dashboards/YYYY-MM-DD/{name}.html
    ↓
[7] 历史 + 可选截图
    → outputs/history/YYYY-MM-DD.json
    → screenshot.py 可选 → PNG（嵌入 PDF）
```

---

## HLZD 三大场景详解

### 场景 ① 销售漏斗图（funnel.js）

**数据格式**：
```json
{
  "stages": [
    {"stage": "询盘", "value": 1000, "conversion_rate": 1.0},
    {"stage": "报价", "value": 500, "conversion_rate": 0.5},
    {"stage": "谈判", "value": 200, "conversion_rate": 0.4},
    {"stage": "成交", "value": 80, "conversion_rate": 0.4}
  ],
  "total_inquiries": 1000,
  "total_deals": 80,
  "overall_conversion": 0.08,
  "period": "2026-07"
}
```

**视觉**：水平梯形拼接（D3 未原生支持 funnel，需自定义 SVG path）
**交互**：hover tooltip（阶段/数量/转化率）+ 点击下钻
**输出**：SVG 嵌入 HTML

### 场景 ② 询盘分析看板（dashboard-quote.js）

**布局**：CSS Grid（6 图组合）

```
┌────────────────┬────────────────┐
│  漏斗图          │  KPI 卡片×3      │
├────────────────┴────────────────┤
│  询盘趋势（折线）                │
├────────────────┬────────────────┤
│  来源分布（饼图）│  转化率（柱）  │
└────────────────┴────────────────┘
```

**响应式**：移动端单列 / 桌面端 2×3 网格
**主题色**：HLZD 蓝绿（`#1890FF` / `#13C2C2`）

### 场景 ③ 客户地理分布（geo-customers.js）

**数据格式**：
```json
{
  "points": [
    {"country": "UAE", "count": 50, "lat": 24.4539, "lng": 54.3773},
    {"country": "Saudi Arabia", "count": 30, "lat": 24.7136, "lng": 46.6753}
  ]
}
```

**渲染**：d3.geoMercator() + world-110m.json TopoJSON
**视觉**：客户数量决定气泡大小 + 颜色深度
**交互**：hover tooltip + 点击国家放大

---

## 输出格式

```
D:\AI-P\skills\hlzd-d3-viz\outputs\
├── dashboards\
│   └── YYYY-MM-DD
│       ├── funnel_2026-07.html
│       ├── dashboard_2026-07.html
│       └── geo_world.html
└── history\
    └── YYYY-MM-DD.json
```

**HTML 自包含**：内嵌 D3.js CDN + topojson.v3 CDN，浏览器直接打开即可。

---

## D3.js + TopoJSON CDN

```html
<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://d3js.org/topojson.v3.min.js"></script>
```

**离线备选**：若 CDN 不可用，`assets/world-110m.json` 已内置世界地图数据。

---

## 限制与边界

### ✅ 适合
- B2B 销售漏斗（询盘转化分析）
- 询盘看板（多图表组合 dashboard）
- 客户地理分布（市场分析）
- 通用图表（柱状/折线/饼图等）

### ❌ 不适合
- 实时数据流（毫秒级更新，D3 重绘开销大）
- 大数据量（>10k 点用 ECharts/Plotly 更合适）
- 3D 可视化（v0.1 不支持）

### ⚠️ 硬限制
- 单次最多 6 图组合（dashboard）
- 地图气泡 ≤ 200 个（视觉清晰度）
- HTML 文件大小 ≤ 5MB

---

## 错误地图

| 异常 | 解决方案 |
|---|---|
| D3.js CDN 不可用 | 改用本地 `assets/d3.v7.min.js` |
| TopoJSON 加载失败 | 检查 `assets/world-110m.json` 是否存在 |
| 字段缺失 | 退回 Demo 数据 + 提示"请补充 X 字段" |
| 数值类型错误 | 强制转 int/float |
| CSV 列名不匹配 | 显式校验 + 友好报错（TODO P1）|
| HTML 文件过大 | 精简数据 + 移除冗余字段 |

---

## 依赖与部署

```bash
# 1. Python 依赖（仅 jinja2）
py -m pip install -r requirements.txt

# 2. D3.js 通过 CDN，无需本地安装
# 浏览器自动加载 https://d3js.org/d3.v7.min.js

# 3. 世界地图（已内置，无需联网）
# assets/world-110m.json（107KB）

# 4. Panmira 安装
mb skills install hlzd-d3-viz 青囊
```

---

## 验证清单

新版本发布前必跑：
- [ ] `mb skills list` 看到 `hlzd-d3-viz`
- [ ] 飞书发"生成 7 月询盘漏斗图" → logs 看到 selected
- [ ] 销售漏斗图（funnel.js）单图测试
- [ ] 询盘分析看板（6 图组合）
- [ ] 客户地理分布（世界地图）
- [ ] B2B 闭环：自动检测最新报告 → 出 dashboard
- [ ] HTML 自包含验证（含 D3.js CDN）
- [ ] 离线模式（本地 D3.js）回退正常
- [ ] 历史 JSON 写入成功

---

## 自动串联

### 上游（被谁触发）
- **HLZD-B2B工业品调研**：报告生成后自动调用出 dashboard
- **hlzd-image-gen**：dashboard 中嵌入产品图

### 下游（触发谁）
- dashboard 生成后 → 可调 hlzd-office-doc 转 PDF（截图嵌入）
- dashboard 生成后 → 可调 hlzd-video-gen 录屏做演示视频
- dashboard 生成后 → 可调 HLZD-email-group 嵌入邮件

### 被动串联
- 历史 JSON 每日统计 + 报表

---

## 已知限制（v0.1 接受）

- D3.js 通过 CDN（v0.2 计划本地化）
- 不支持实时数据流（v0.2 计划）
- 不支持 3D 可视化（v0.3 计划）
- 不支持数据导出 CSV（v0.2 计划）
- screenshot.py 测试覆盖 0%（TODO）

---

## 后续路线（v0.2+）

| 版本 | 新增 |
|---|---|
| v0.2 | 本地化 D3.js（离线模式）|
| v0.2 | 实时数据流（SSE）|
| v0.2 | 数据导出 CSV/PNG/PDF |
| v0.3 | 3D 可视化（three.js 集成）|
| v0.3 | 仪表盘模板库（销售/财务/库存）|
| v0.4 | AI 自动洞察（基于历史数据生成文字分析）|