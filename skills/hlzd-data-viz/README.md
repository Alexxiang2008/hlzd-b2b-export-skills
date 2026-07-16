# HLZD-D3可视化 Skill

> B2B 数据可视化 skill。基于 D3.js v7 + chrisvoncsefalvay/claude-d3js-skill 通用图表。
> HLZD 特色场景：销售漏斗图、询盘分析看板、客户地理分布。

**版本**: v0.1.0
**发布**: 2026-07-06
**所有者**: 深圳海联智达科技有限公司（HLZD）

---

## 🎯 适用场景

- 销售漏斗图（询盘 → 报价 → 谈判 → 成交 转化率）
- 询盘分析看板（多图表组合 dashboard）
- 客户地理分布（世界/中国地图 + 气泡）
- 通用 D3 图表（折线/柱状/热力/饼图等）

---

## 🚀 5 分钟快速开始

### 1. 安装 Python 依赖

```bash
cd "D:\AI-P\skills\HLZD-D3可视化"
py -m pip install jinja2
```

### 2. 让 Claude Code 识别 skill

```bash
xcopy /E /I /Y "scripts" "C:\Users\13864\.claude\skills\HLZD-D3可视化\scripts"
xcopy /E /I /Y "presets" "C:\Users\13864\.claude\skills\HLZD-D3可视化\presets"
xcopy /E /I /Y "data" "C:\Users\13864\.claude\skills\HLZD-D3可视化\data"
xcopy /E /I /Y "assets" "C:\Users\13864\.claude\skills\HLZD-D3可视化\assets"
xcopy /E /I /Y "references" "C:\Users\13864\.claude\skills\HLZD-D3可视化\references"
copy /Y "SKILL.md" "C:\Users\13864\.claude\skills\HLZD-D3可视化\SKILL.md"
```

### 3. 验证安装

```bash
# 5 个脚本 --help
py scripts/data_loader.py --help
py scripts/html_builder.py --help
py scripts/output_manager.py --help
py scripts/orchestrator.py --help
```

---

## 💡 使用示例

### 方式 A：跟 Claude Code 直接对话

```
你： 给销售团队生成 7 月询盘分析看板

Claude：
  → 调用 HLZD-B2B工业品调研 skill 加载询盘数据
  → 触发 HLZD-D3可视化 skill 生成 dashboard
  → 输出 outputs/dashboards/2026-07-06/dashboard_*.html
  → 你在浏览器打开 → 看到 6 图组合看板
```

### 方式 B：手动 orchestrator 调用

```bash
# 销售漏斗图
py scripts/orchestrator.py --chart-type funnel --source demo --lang zh_CN

# 询盘分析看板
py scripts/orchestrator.py --chart-type dashboard --data-file data/dashboard-sample.json

# 客户地理分布
py scripts/orchestrator.py --chart-type geo --data-file data/geo-sample.json

# B2B 闭环
py scripts/orchestrator.py --auto-b2b --chart-type dashboard
```

### 方式 C：HTML → PNG 嵌入 PDF

```bash
py scripts/screenshot.py \
  --input outputs/dashboards/2026-07-06/dashboard_*.html \
  --output /tmp/dashboard.png

# 然后用 HLZD-办公文档 skill 把 PNG 嵌入 PDF
```

---

## 📁 目录结构

```
HLZD-D3可视化/
├── SKILL.md                                # NLU 提示词 + 工作流
├── requirements.txt                        # 0 个 pip 依赖
├── .env.example
├── .gitignore
├── scripts/                                # 5 个 Python 脚本
│   ├── data_loader.py                      # 数据接入
│   ├── html_builder.py                     # HTML 模板生成
│   ├── output_manager.py                   # 历史 JSON
│   ├── orchestrator.py                     # ⭐ 主调度
│   └── screenshot.py                       # HTML → PNG（可选）
├── presets/                                # JavaScript 图表
│   ├── colors.js                           # HLZD 品牌色
│   ├── utils.js                            # 共享工具
│   ├── common/                              # 通用图表
│   │   ├── bar.js
│   │   ├── line.js
│   │   ├── pie.js
│   │   └── heatmap.js
│   └── hlzd/                                # ⭐ HLZD 特色
│       ├── funnel.js                        # 销售漏斗
│       ├── dashboard-quote.js               # 询盘看板
│       └── geo-customers.js                 # 客户地理
├── data/                                    # 示例数据
│   ├── funnel-sample.json
│   ├── dashboard-sample.json
│   └── geo-sample.json
├── assets/                                  # 静态资源（地图）
│   └── world-110m.json (Phase 2 下载)
├── references/                              # 文档
│   └── core-workflow.md
├── outputs/                                  # 运行时生成
│   ├── dashboards/
│   └── history/
└── tests/
    └── test_e2e.md
```

---

## 🔧 故障排查

| 问题 | 解决方案 |
|------|---------|
| `python` 命令报 Exit code 49 | Windows Store 劫持，用 `py` launcher |
| Jinja2 未安装 | `py -m pip install jinja2` |
| D3.js CDN 不可用 | 本地化 D3.js 到 assets/ |
| 世界地图加载失败 | 自动降级为散点图（无报错）|
| 截图失败 | Playwright 未装，可选 |

---

## 📞 支持

- **项目所有者**：深圳海联智达科技有限公司（HLZD）
- **问题反馈**：内部 Slack #hlzd-skills

---

## 📄 许可证

内部使用，未经授权禁止外部分发。

---

**v0.1.0 状态**：MVP 完成。可投产（D3.js CDN + Python Jinja2 即可）。Phase 2 增加 Playwright 截图 + 地图数据下载 + pytest 自动化测试。