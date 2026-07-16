# HLZD-D3可视化 - E2E 测试用例

本文件包含 8 条 e2e 测试用例。

---

## 测试 1：环境就绪

```bash
cd "D:\AI-P\skills\HLZD-D3可视化"

# Python 依赖（jinja2 已在 HLZD-办公文档 requirements）
py -m pip install jinja2

# D3.js 通过 CDN（无需本地安装）
# 浏览器访问 https://d3js.org/d3.v7.min.js 应返回 200

# Smoke test 5 个脚本
py scripts/data_loader.py --help
py scripts/html_builder.py --help
py scripts/output_manager.py --help
py scripts/orchestrator.py --help
```

通过：5 个脚本输出 usage。

---

## 测试 2：销售漏斗图（Demo 数据）

```bash
py scripts/orchestrator.py --chart-type funnel --source demo --lang zh_CN
# 输出：outputs/dashboards/2026-07-06/funnel_demo_20260706.html
# 双击 HTML → 浏览器 → 看到销售漏斗图
```

通过：HTML 自包含，可在浏览器打开。

---

## 测试 3：询盘分析看板

```bash
py scripts/orchestrator.py --chart-type dashboard --data-file data/dashboard-sample.json --lang zh_CN
# 输出：6 图组合 dashboard HTML
```

通过：dashboard 显示漏斗 + KPI + 趋势 + 来源 + 转化率 + 地理。

---

## 测试 4：B2B 闭环（HLZD-B2B工业品调研 → 看板）

```bash
py scripts/orchestrator.py --auto-b2b --chart-type dashboard --lang zh_CN
# 自动检测 HLZD-B2B工业品调研 最新报告 → 解析 → 渲染 dashboard
```

通过：dashboard 显示真实询盘数据（非 Demo）。

---

## 测试 5：客户地理分布

```bash
py scripts/orchestrator.py --chart-type geo --data-file data/geo-sample.json --lang en_US
# 输出：世界地图（含客户气泡）
# 若 world-110m.json 不存在 → 降级为散点图
```

通过：地图加载或降级散点都正常。

---

## 测试 6：自定义数据（用户 JSON）

```bash
cat > /tmp/my_funnel.json << 'EOF'
{
  "stages": [
    {"stage": "Inquiry", "value": 800},
    {"stage": "Quote", "value": 400},
    {"stage": "Negotiation", "value": 150},
    {"stage": "Won", "value": 60}
  ],
  "total_inquiries": 800, "total_deals": 60, "overall_conversion": 0.075
}
EOF

py scripts/orchestrator.py --chart-type funnel --source user_json --data-file /tmp/my_funnel.json
```

通过：使用用户数据生成漏斗。

---

## 测试 7：HTML 自包含验证

```bash
# 检查输出 HTML 是否包含 D3.js CDN
grep "d3js.org/d3" outputs/dashboards/2026-07-06/*.html
# 应能看到：<script src="https://d3js.org/d3.v7.min.js">
```

通过：CDN script 标签存在。

---

## 测试 8：HTML → PNG 截图（可选）

```bash
# 安装 Playwright（首次）
py -m pip install playwright
playwright install chromium

# 截图（用于嵌入 HLZD-办公文档 PDF）
py scripts/screenshot.py --input outputs/dashboards/2026-07-06/dashboard_*.html --output /tmp/dashboard.png
```

通过：PNG 文件生成。

---

## 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| D3.js CDN 加载失败 | 网络问题 | 本地化 D3.js 到 assets/d3.v7.min.js |
| world-110m.json 加载失败 | 文件缺失 | 用降级散点图（自动）|
| Jinja2 未安装 | pip 缺失 | `py -m pip install jinja2` |
| Playwright 未安装 | 截图可选 | 默认输出 HTML，可忽略 |
| 中文乱码 | 浏览器编码 | 确保 HTML 头部 `<meta charset="UTF-8">` |
