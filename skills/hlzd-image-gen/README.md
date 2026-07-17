# HLZD-图片生成 Skill

> B2B 工业品 AI 生图 skill。基于 Agnes Image 2.1 Flash（云端 T2I/I2I）+ rembg（本地抠图）。
> 专攻机械/设备/建材等 B2B 工业品场景，支持 T2I（文生图）/I2I（图生图）/抠图（白底图）三种能力。
> 与 HLZD-B2B工业品调研 skill 全链路闭环。

**版本**: v0.1.0
**发布**: 2026-07-06
**所有者**: 深圳海联智达科技有限公司（HLZD）

---

## 🎯 适用场景

- B2B 工业品主图、场景图、细节图（机械/设备/建材/零件/工具）
- 商品图抠图（白底图、透明 PNG）
- 参考图风格迁移（保留工业质感）
- 与 HLZD-B2B工业品调研 闭环配图

---

## 🚀 5 分钟快速开始

### 1. 安装依赖

```bash
# 注意：用 `py -m pip` 而非 `pip`，避免 Python 3.13/3.14 错位
py -m pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# Windows CMD
copy .env.example .env

# 或 Git Bash
cp .env.example .env
```

然后编辑 `.env`，填入你的 `AGNES_API_KEY`：

```ini
AGNES_API_KEY=sk-your-real-key-here
AGNES_ENDPOINT=https://apihub.agnes-ai.com/v1/images/generations
AGNES_MODEL=agnes-image-2.1-flash
```

> **⚠️ 安全提醒**：
> - `.env` 已加入 `.gitignore`，不会被 git 跟踪
> - 但若你手动初始化 git 仓库，请确认 `.gitignore` 生效
> - 推荐做法：把 `AGNES_API_KEY` 配置到系统环境变量，而非项目级 `.env`

### 3. 让 Claude Code 识别 skill

Claude Code 扫描 `C:\Users\13864\.claude\skills\` 下的所有 `SKILL.md`。所以要把本 skill 同步过去：

```bash
# Windows CMD
xcopy /E /I /Y "scripts" "C:\Users\13864\.claude\skills\HLZD-图片生成\scripts"
xcopy /E /I /Y "presets" "C:\Users\13864\.claude\skills\HLZD-图片生成\presets"
xcopy /E /I /Y "references" "C:\Users\13864\.claude\skills\HLZD-图片生成\references"
copy /Y "SKILL.md" "C:\Users\13864\.claude\skills\HLZD-图片生成\SKILL.md"

# 不要复制 .env！扫描目录的 .env 会被 Claude Code 扫描，可能泄露
```

### 4. 验证安装

```bash
# 6 个脚本的 --help 都应成功
py scripts/agnes_client.py --help
py scripts/prompt_builder.py --help
py scripts/b2b_research_parser.py --help
py scripts/image_enhancer.py remove-bg --help
py scripts/output_manager.py --help
py scripts/orchestrator.py --help
```

通过：6 个脚本全部输出 usage 文档。

---

## 💡 使用示例

### 方式 A：跟 Claude Code 直接对话

```
你：给石油套管生成一张阿里国际站白底主图

Claude：
  → 识别产品（套管）+ 调用 NLU 解析
  → 检测到是工业品，触发 Step 2.5 专业访谈
  → 调用 AskUserQuestion 问 5 个参数：
    - 钢级？A.J55 / B.N80 / C.L80 / D.P110 / E.不指定
    - 外径？A.4-1/2" / B.5-1/2" / C.7" / D.9-5/8" / E.不指定
    - 扣型？A.BTC / B.LTC / C.STC / D.Premium / E.不指定
    - 端部？A.绿色保护套 / B.黄漆 / C.裸端 / D.不指定
    - 长度？A.R2 / B.R3 / C.不指定
  → 用户回答：P110 / 7" / BTC / 绿保护套 / R2
  → 展示理解回执（Markdown 表格）
  → 用户确认
  → 生图（约 5-15 秒）
  → 输出图 + 历史 JSON
```

### 方式 B：手动构造 entities + 调用脚本

```bash
# 1. 构造 entities.json
cat > entities.json << 'EOF'
{
  "product_name": "阀门",
  "product_category": "machinery",
  "capability": "t2i",
  "scene": "on display at oil industry trade show booth",
  "size": "1024x1024",
  "expert_answers": {
    "valve_type": "ball valve",
    "pressure_class": "300#",
    "connection_type": "flanged",
    "body_material": "CF8 stainless steel 304",
    "operation": "manual handwheel"
  }
}
EOF

# 2. 调用 orchestrator
py scripts/orchestrator.py --entities entities.json --capability t2i

# 输出：
# - D:\AI-P\skills\HLZD-图片生成\outputs\generated\YYYY-MM-DD\阀门_001.png
# - D:\AI-P\skills\HLZD-图片生成\outputs\history\YYYY-MM-DD.json
```

### 方式 C：B2B 闭环（一键配图）

```bash
# 前提：HLZD-B2B工业品调研 已生成某产品报告
py scripts/orchestrator.py --auto-b2b --capability t2i
# 自动检测最新报告 → 解析 → 补全 entities → 生图
```

### 方式 D：商品抠图（rembg 本地）

```bash
# 抠图 + 输出透明 PNG
py scripts/image_enhancer.py remove-bg --input D:\test\valve.jpg --output D:\test\valve_no_bg.png

# 抠图 + 换白底
py scripts/image_enhancer.py change-bg --input D:\test\valve.jpg --bg-color "#ffffff" --output D:\test\valve_white.png
```

### 方式 E：I2I（图生图，本地参考图）

```bash
# 用本地参考图（自动转 base64 data URI）
py scripts/orchestrator.py --entities entities.json --capability i2i --reference D:\test\reference.jpg
```

---

## 📁 目录结构

```
HLZD-图片生成/
├── SKILL.md                                # Claude Code NLU 提示词 + 工作流
├── README.md                                # 本文件（使用指南）
├── requirements.txt                        # Python 依赖
├── .env.example                            # API Key 模板（不含真实 Key）
├── .gitignore                                # 排除 .env / outputs / __pycache__
├── scripts/                                # 6 个 Python 脚本
│   ├── agnes_client.py                     # Agnes API 客户端（T2I/I2I + 重试）
│   ├── prompt_builder.py                   # NLU 输出 + preset → 结构化 prompt
│   ├── b2b_research_parser.py              # HLZD-B2B工业品调研 报告解析
│   ├── image_enhancer.py                   # rembg 抠图（本地）
│   ├── output_manager.py                   # 保存图片 + JSON 历史
│   └── orchestrator.py                     # 主调度（SKILL.md 调用入口）
├── presets/                                # 6 个 YAML preset
│   ├── industrial/
│   │   ├── machinery.yaml                  # 机械（套管/阀门/轴承/工具）
│   │   ├── equipment.yaml                  # 设备（集装箱/工程机械/发电机）
│   │   └── materials.yaml                  # 建材（钢结构/铝合金/塑料管）
│   └── common/
│       ├── angles.yaml                     # 视角（front/45deg/overhead/cutaway/detail）
│       ├── lighting.yaml                   # 光照（studio/natural/dramatic/softbox）
│       └── styles.yaml                     # 风格（photorealistic/catalog/technical/3d-render）
├── references/                             # 4 个文档
│   ├── nlu-schema.md                       # NLU 实体抽取 + 追问模板
│   ├── preset-catalog.md                   # preset 速查表
│   ├── agnes-api-guide.md                  # Agnes API 速查
│   └── b2b-closed-loop-guide.md            # B2B 闭环调用示例
└── tests/
    └── test_e2e.md                          # 5 条 e2e 测试用例
```

---

## 🔧 故障排查

| 问题 | 解决方案 |
|---|---|
| `python` 命令报 Exit code 49 | Windows Store 劫持，用 `py` launcher |
| Agnes HTTP 401 | 检查 `.env` 中 `AGNES_API_KEY` 是否正确 |
| rembg 首次报"model not found" | 联网，rembg 会自动下载 ~170MB 模型到 `%USERPROFILE%\.u2net\` |
| B2B 报告未找到 | 检查 `HLZD-B2B工业品调研` 目录路径，或用 `--report` 显式指定 |
| `py` 找不到包但 `pip` 装了 | 用 `py -m pip install` 而非 `pip install`（避免 Python 3.13/3.14 错位）|
| 输出乱码 | 所有脚本已内置 UTF-8 wrapper，无需处理 |

---

## 📊 性能 & 成本

| 项 | 数据 |
|---|---|
| 单图耗时 | 5-15 秒（同步阻塞）|
| Agnes 标准价格 | $0.003/图 |
| Agnes 当前促销价 | $0/图（限时期）|
| 并发生图 | 不支持（quantity>1 是串行）—— TODO C7 |
| 批量建议 | quantity ≤ 4（避免长等待）|

---

## 🔒 安全

- `.env` 已加入 `.gitignore`，不会被 git 跟踪
- 推荐：把 `AGNES_API_KEY` 配到用户级环境变量（`%USERPROFILE%\.env\HLZD.env`）而非项目 `.env`
- I2I 参考图 URL 应限制只允许图床域名（TODO 安全加固）
- 不要把 `.env` 复制到 Claude Code 扫描目录（`C:\Users\13864\.claude\skills\`）

---

## 🛠️ 开发 & 测试

```bash
# Smoke test
for script in agnes_client prompt_builder b2b_research_parser image_enhancer output_manager orchestrator; do
  py scripts/${script}.py --help 2>&1 | head -1
done

# E2E 测试
py scripts/b2b_research_parser.py --auto --out /tmp/b2b.json
py scripts/orchestrator.py --entities /tmp/b2b.json --capability t2i

# 详细测试用例：见 tests/test_e2e.md
```

---

## 📞 支持

- **项目所有者**：深圳海联智达科技有限公司（HLZD）
- **问题反馈**：内部 Slack #hlzd-skills
- **详细文档**：见 `SKILL.md` 和 `references/` 目录

---

## 📄 许可证

内部使用，未经授权禁止外部分发。

---

**v0.1.0 状态**：MVP 完成，CEO review 评分 7.5/10，可投产。后续版本将增加单元测试、并发优化、ImageProvider 抽象层。