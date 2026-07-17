---
name: hlzd-product-video-gen
description: "B2B 工业品营销视频生成 —— 图生视频（I2V）/ 多段拼接 18 秒 / BGM / 字幕。Agnes Video V2.0 + FFmpeg。6 种 preset（设备/机械/材料）+ i18n 字幕目录。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: content-asset
  triggered_by:
    - 生视频
    - 生成视频
    - 文生视频
    - 图生视频
    - T2V
    - I2V
    - 产品视频
    - 工业品视频
    - 阿里国际站视频
    - TikTok短视频
    - 营销视频
    - 产品演示视频
    - 安装视频
    - 工厂实拍
    - 动画演示
    - 视频拼接
    - 多段拼接
    - 自动字幕
    - 英文视频
    - generate video
    - industrial video ad
    - marketing video
---

# hlzd-video-gen — B2B 工业品 AI 生视频

> 解决 B2B 工业品视频问题：产品细节展示 + 应用场景演示 + 平台规格 + BGM/字幕一体化。

---

## Quick Commands

```bash
# I2V 图生视频（主路径，自动从 hlzd-image-gen 取最新 PNG）
hlzd-video-gen "石油套管" --duration 10 --style "白底"

# 多图 I2V（把多张图合成一段演示视频）
hlzd-video-gen --multi-image "D:\img1.jpg,D:\img2.jpg,D:\img3.jpg" --duration 15

# 关键帧动画（A 图过渡到 B 图）
hlzd-video-gen --keyframes "D:\start.jpg,D:\end.jpg" --duration 12

# T2V 文生视频（无任何素材时的备用）
hlzd-video-gen --t2v "石油套管在油田作业的航拍镜头" --duration 10

# 阿里国际站竖版短视频（30 秒，多段拼接）
hlzd-video-gen "石油套管" --duration 30 --aspect 9:16 --platform alibaba

# B2B 闭环（自动检测最新报告 + 最新产品图）
hlzd-video-gen --auto-b2b --duration 15

# BGM + 字幕（中英对照，默认英文）
hlzd-video-gen "石油套管" --duration 10 --bgm industrial --subtitle bilingual

# CLI 底层调用
py scripts/orchestrator.py --entities entities.json --mode i2v
```

---

## 定位

| 对比项 | 通用视频 AI（Sora/可灵） | hlzd-image-gen（静态） | **hlzd-video-gen** |
|---|---|---|---|
| 适用场景 | 创意/娱乐/消费品 | 静态主图 | **B2B 工业品营销视频** |
| 起点 | 文生视频 | 文生图 | **图生视频（I2V）为主，复用图片 skill 素材** |
| 一致性 | 单条独立 | 多角度图保持一致 | **产品视觉跨图/跨视频一致** |
| 输出 | 短视频无音轨 | PNG/JPG | **MP4 + BGM + 字幕，平台规格** |
| 合规 | 宽松 | 白底图 + 无 LOGO | **多镜头不出现版权元素** |
| 生态 | 独立工具 | 与 B2B 调研闭环 | **图片→视频→邮件 全链路** |

**核心原则**：B2B 工业品视频不是"炫技"，是"产品细节展示 + 应用场景演示 + 平台规格适配"。

---

## 核心能力矩阵

| 能力 | 实现 | 适用场景 | 单段耗时 |
|---|---|---|---|
| **I2V**（图生视频·单图）| Agnes Video V2.0 | 产品 360°展示、白底主图延伸 | 30-90s |
| **多图 I2V** | Agnes Video V2.0 | 安装流程演示、工艺前后对比 | 60-120s |
| **关键帧动画** | Agnes Video V2.0 | 产品特写镜头切换、场景过渡 | 60-120s |
| **T2V**（文生视频·备用）| Agnes Video V2.0 | 无任何素材时的应急 | 30-90s |
| **多段拼接** | FFmpeg xfade | >18s 自动分段拼接 | 5-15s |
| **BGM 自动合成** | FFmpeg amix + 内置素材库 | 企业宣传/工业节奏 | 2-5s |
| **字幕烧录** | FFmpeg drawtext | 中/英/双语字幕 | 2-5s |

**何时用哪种**：

| 用户表达 | 路由 |
|---|---|
| "给 XX 生成视频" + 已有图 | I2V（默认）|
| "把这几张图合成视频" | 多图 I2V |
| "从 A 图过渡到 B 图" | keyframes |
| "无任何图，文字描述生成" | T2V（最后选择）|

---

## 数据源

| 数据源 | 用途 | 费用 | 备注 |
|---|---|---|---|
| Agnes Video V2.0 | 4 种视频生成模式 | 当前 $0/秒（限时），标准 $0.005/秒 | 单段最长 18s |
| FFmpeg | 本地拼接 / BGM / 字幕 | 免费 | 系统级依赖 |
| hlzd-image-gen | 闭环输入（产品图）| 免费 | 自动检测最新 PNG |
| HLZD-B2B工业品调研 | 闭环输入（产品/HS/市场）| 免费 | 智能检测最新报告 |

---

## 工作流（主流程）

```
输入（产品/时长/风格 + 可选图片/报告）
    ↓
[1] NLU 解析（Claude 自身）
    → 实体抽取（mode/duration/aspect/platform/style/bgm/subtitle）
    → 追问缺失字段
    ↓
[2] 模式路由
    ├─ I2V（默认）→ 自动从 hlzd-image-gen 取最新 PNG
    ├─ 多图 I2V → 多张 PNG 按顺序生成
    ├─ 关键帧 → A 图 → B 图过渡
    └─ T2V（备用）→ 纯文字生成
    ↓
[3] B2B 闭环检测（可选）
    → 智能检测 HLZD-B2B工业品调研 最新报告
    → 自动补充 prompt 上下文
    ↓
[4] 展示理解回执（Markdown 表格）
    ↓
[5] 调用 Agnes API
    → 单段最长 18s（硬限制）
    → >18s 自动分段拼接
    ↓
[6] FFmpeg 后处理
    → 多段拼接（xfade 过渡）
    → BGM 混音（amix）
    → 字幕烧录（drawtext，中英/双语）
    ↓
[7] 输出 + 历史
    → outputs/videos/YYYY-MM-DD/{product}_{seq}.mp4
    → outputs/history/YYYY-MM-DD.json
```

---

## BGM 库（内置 4 风格）

| 风格 | 节奏 | 适用场景 |
|---|---|---|
| **industrial**（默认）| 中速，金属感 | 工厂/设备/工业品 |
| **corporate** | 中速，正能量 | 公司介绍/品牌宣传 |
| **energetic** | 快速，活力 | TikTok 短视频 |
| **calm** | 慢速，舒缓 | 安装演示/工艺流程 |

BGM 素材位于 `assets/bgm/` 目录（4 个 MP3，约 30s/段）。

---

## 输出格式

```
D:\AI-P\skills\hlzd-video-gen\outputs\
├── videos\
│   └── YYYY-MM-DD\
│       └── {产品名}_{seq}.mp4
└── history\
    └── YYYY-MM-DD.json
```

**平台规格预设**：
- 阿里国际站：1:1 或 4:3，10-30s，竖版 9:16
- TikTok：9:16，15-60s
- YouTube Shorts：9:16，<60s
- 官网/画册：16:9，30-60s
- 邮件附件：1:1 或 4:3，<30s（避免大文件）

---

## 限制与边界

### ✅ 适合
- B2B 工业品营销视频（产品展示、流程演示、场景应用）
- 阿里国际站 / TikTok 短视频
- 与 hlzd-image-gen 协同（图生视频）

### ❌ 不适合
- 真人出镜（合规风险 + 模型效果差）
- 长视频（>60s 多段拼接画质衰减）
- 实时直播
- 复杂叙事/剧情（AI 视频模型不擅长）

### ⚠️ 硬限制
- Agnes 单段最长 18 秒（超长需分段拼接）
- 单次批量 ≤ 8 段
- 单段超时 5 分钟自动重试 2 次
- 字幕烧录需系统装中文字体

---

## 错误地图

| 异常 | 解决方案 |
|---|---|
| Agnes HTTP 401 | 检查 `.env` 中 `AGNES_API_KEY` |
| Agnes HTTP 429 | 自动重试 2 次（指数退避）|
| Agnes 18s 硬限制 | 自动分段 + FFmpeg xfade 拼接 |
| FFmpeg 未找到 | 安装 FFmpeg + 加 PATH |
| 中文字体缺失 | 下载 `NotoSansCJK-Regular.ttc` 到 `assets/fonts/` |
| hlzd-image-gen 无最新图 | 用户需先生图，或用 T2V 兜底 |
| 视频文件过大（>100MB）| 降低码率 / 缩短时长 |

---

## 依赖与部署

```bash
# 1. Python 依赖
py -m pip install -r requirements.txt

# 2. FFmpeg（系统级依赖）
# Windows: https://ffmpeg.org/download.html
# Mac: brew install ffmpeg
# Linux: apt install ffmpeg

# 3. 中文字体（字幕烧录）
# 下载 NotoSansCJK-Regular.ttc 到 assets/fonts/

# 4. 配置 .env
copy .env.example .env
# 编辑 .env，填入 AGNES_API_KEY=your_key

# 5. Panmira 安装
mb skills install hlzd-video-gen 青囊
```

---

## 验证清单

新版本发布前必跑：
- [ ] `mb skills list` 看到 `hlzd-video-gen`
- [ ] 飞书发"给石油套管生成 10 秒视频" → logs 看到 selected
- [ ] I2V 单段测试（30-90s 出片）
- [ ] 多图 I2V（多张 PNG 合成）
- [ ] 18s+ 自动分段拼接
- [ ] BGM 混音（4 风格）
- [ ] 字幕烧录（中/英/双语）
- [ ] B2B 闭环：自动检测最新报告 + 最新图 → 出视频
- [ ] 历史 JSON 写入成功

---

## 自动串联

### 上游（被谁触发）
- **hlzd-image-gen**：生图后自动调用本 skill 做图生视频
- **HLZD-B2B工业品调研**：报告生成后自动调用出营销视频
- **HLZD-email-group**：邮件需要视频附件时调用本 skill

### 下游（触发谁）
- 视频生成后 → 可调 HLZD-email-group 嵌入邮件
- 视频生成后 → 可调 hlzd-d3-viz 嵌入 dashboard

### 被动串联
- 历史 JSON 每日统计 + 报表

---

## 已知限制（v0.1 接受）

- Agnes 仅一个模型（V2.0），无降级链
- 单 API 依赖（Agnes Video V2.0），无容灾 fallback
- 不支持实时流媒体
- 不支持人物语音合成（v0.2 规划）

---

## 后续路线（v0.2+）

| 版本 | 新增 |
|---|---|
| v0.2 | 接入可灵 / 通义万相作为降级链 |
| v0.2 | TTS 语音合成（中/英/俄/阿）|
| v0.3 | 实时海运/工厂视频拼接 |
| v0.3 | 阿里国际站 / TikTok 自动发布 |
| v0.4 | 多镜头自动剪辑（基于 B2B 报告章节）|