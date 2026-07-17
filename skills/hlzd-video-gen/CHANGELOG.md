# Changelog

所有 HLZD-视频生成 skill 的重要变更都会记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [0.1.0] - 2026-07-06

### 🎉 MVP 发布

首个可发布版本。覆盖 B2B 工业品视频营销全链路：报告 → 配图 → 视频 → 字幕 → BGM。

### ✨ 新增

- **4 种 Agnes Video V2.0 生成模式**（scripts/agnes_video_client.py）
  - T2V 文生视频（备用）
  - I2V 图生视频（主路径）
  - 多图 I2V（首尾帧控制）
  - 关键帧动画（场景过渡）
- **B2B 闭环解析**（scripts/b2b_research_parser.py）
  - 自动检测 HLZD-B2B工业品调研 最新报告
  - 自动检测 HLZD-图片生成 历史 PNG
- **图片skill 闭环**
  - 一键读取图片skill outputs/generated/ 最新图
- **图床集成**（scripts/imgbb_uploader.py）
  - 本地 PNG → imgbb → 公网 URL（I2V 必需）
- **质量评分器**（scripts/quality_scorer.py）
  - 5 维度评分：大小/分辨率/时长/码率/帧数
- **多次生成 + 自动选最佳**（orchestrator.py）
  - 同一 prompt 跑 N 次，自动按分数选最优
  - CLI 参数 `--num-candidates N`
- **I2V 一键全流程**
  - CLI `--reference-image` 直接传本地 PNG
  - 自动检测本地/公网 URL
  - 兼容 multi_i2v / keyframes 多图模式
- **多段拼接**（video_postprocess.py）
  - 突破 Agnes 单段 18s 硬上限
  - 自动按场景拆段 + xfade 黑场过渡
- **BGM 混音**（video_postprocess.py）
  - 4 种风格：corporate / industrial / upbeat / epic
  - 自动循环到视频时长
- **中英字幕**（subtitle_manager.py + i18n_catalog.yaml）
  - 默认英文（出海优先）
  - 中英对照表（按需追加）
  - 字体自动 fallback（思源黑体 / Arial）
- **6 类 B2B preset**
  - 9 种镜头动作
  - 8 种场景预设
  - 机械 / 设备 / 建材 三类产品
  - 每个产品带 HS 编码和 default 配置

### 🐛 修复（开发过程）

1. UTF-8 stdout wrapper 在 import 链中重复 wrap 导致 `I/O operation on closed file`
2. Agnes API 视频URL 字段从 `remixed_from_video_id` 改名为 `url`（兼容）
3. subprocess 在 Windows 上用 GBK 解码 FFmpeg stderr 中文失败
4. FFmpeg drawtext 字体路径冒号 `:` 被当 filter 分隔符
5. append_history 函数期望 entry 含 `date` 字段缺失
6. I2V 模式只支持 1 张图，CLI capability 被 prompt_builder 自动升级为 multi_i2v
7. 多次生成时 candidates 记录不全 + 次优未清理

### ⚠️ 已知限制

- **单段 18 秒硬上限**（Agnes API 限制）：>18s 需多段拼接
- **质量天花板**：Agnes 训练数据对 B2B 行业缩写不熟（OCTG 偶发错字）
- **单 API 依赖**：100% 依赖 Agnes Video V2.0（容灾见 TODO）
- **限时免费**：Agnes 当前 $0/秒，标准 $0.005/秒
- **公网图片**：I2V 需公网 URL，本地 PNG 通过 imgbb 中转

### 🎯 沉淀的最佳实践

详见 `references/quality-optimization.md`：
- 管材/型材类默认 `push_in` 镜头（避免 3D 旋转变形）
- 行业缩写产品 preset 加 `extra_negative_en`（防错字）
- 全局 negative 加 "no text overlay, no labels, no watermarks"

### 📊 测试覆盖

详见 `tests/test_e2e.md`（11 个 E2E 用例 T1-T11）：
- T1.1 T2V 冒烟测试 ✅
- T1.2 I2V 真图测试 ✅
- T2 中英字幕生成 ✅
- T6 Prompt 拼装 ✅
- T7 B2B 闭环解析 ✅
- T8 Orchestrator 端到端（T2V） ✅
- T8 Orchestrator 端到端（I2V 完整） ✅
- T8 Orchestrator 端到端（多次生成+选最佳） ✅
- T8 Orchestrator 端到端（I2V 一键） ✅
- T8 Orchestrator 端到端（I2V 一键+3 候选联动） ✅
- T11 质量优化（管材 OCTG 案例） ✅

### 🗂️ 文件清单（22 个文件，4047+ 行）

- SKILL.md（708 行）
- 6 个 Python 脚本（2201 行）
- 6 个 YAML preset
- 3 个 Markdown 参考文档
- 1 个 CHANGELOG.md
- 1 个 VERSION
- 4 个配置文件
- 1 个 .gitignore

---

## 后续版本规划（NOT in scope）

- 0.2.0：失败自动重试 + 备用 API（TODO 3）
- 0.3.0：横向扩品类（建材+消费品 preset）
- 0.4.0：成本统计 + 预算告警
- 1.0.0：LoRA 微调 B2B 行业模型（待 ROI 验证）
