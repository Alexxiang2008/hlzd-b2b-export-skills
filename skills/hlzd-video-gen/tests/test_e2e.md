# HLZD-视频生成 - 端到端测试用例

> **前置条件**：
> 1. `.env` 已配置 `AGNES_API_KEY=ag-xxx`
> 2. FFmpeg 已安装并在 PATH 中
> 3. （可选）`assets/bgm/*.mp3` 至少 1 个
> 4. （可选）`assets/fonts/*.ttf` 至少 1 个
> 5. （可选）HLZD-图片生成 已生成至少 1 张产品图

---

## 测试矩阵

| # | 用例 | 前置 | 预期 |
|---|------|------|------|
| T1 | Agnes 客户端 4 种模式 | API Key | 创建任务 + 轮询完成 + 下载 MP4 |
| T2 | 字幕生成器 中/英/双语 | preset 完整 | 输出有效字幕 JSON |
| T3 | 视频拼接 | 2 段 MP4 | 输出 1 段 MP4 + xfade |
| T4 | BGM 混音 | MP4 + BGM | 输出有背景音乐 MP4 |
| T5 | 字幕烧录 | MP4 + 字幕 | 输出有字幕 MP4 |
| T6 | Prompt 构造器 | entities JSON | 输出完整 prompt JSON |
| T7 | B2B 闭环 parser | 报告 markdown | 输出 entities JSON |
| T8 | Orchestrator 全流程 | entities | 输出最终 MP4 + 历史 |
| T9 | 图片skill 历史检测 | HLZD-图片生成 | 输出参考图列表 |
| T10 | 18 秒以上自动拼接 | entities duration=30 | 输出 ≥ 25s MP4 |
| **T11** | **质量优化（管材类）** | **参考图 + 优化 preset** | **无几何变形 + 文字正确** |

---

## T1：Agnes 客户端 4 种模式

### T1.1 文生视频（T2V）
```bash
py scripts/agnes_video_client.py \
  --capability t2v \
  --prompt "A professional industrial valve on white background, slow rotation, studio lighting" \
  --duration 5 \
  --aspect-ratio 1:1 \
  --output outputs/test/t2v_test.mp4
```

**预期**：
- 创建任务成功（输出 `video_id`）
- 30-90 秒内完成
- 下载到 `outputs/test/t2v_test.mp4`
- 文件大小 1-10 MB

### T1.2 图生视频（I2V）
```bash
# 准备 1 张公网可访问的产品图 URL
py scripts/agnes_video_client.py \
  --capability i2v \
  --prompt "The valve slowly rotates 360 degrees, white background, studio lighting" \
  --image "https://example.com/valve.png" \
  --duration 8 \
  --output outputs/test/i2v_test.mp4
```

**预期**：单段视频，无音频

### T1.3 多图I2V
```bash
py scripts/agnes_video_client.py \
  --capability multi_i2v \
  --prompt "Smooth transition between product angles" \
  --images "https://example.com/valve_1.png,https://example.com/valve_2.png,https://example.com/valve_3.png" \
  --duration 10 \
  --output outputs/test/multi_test.mp4
```

**预期**：使用 extra_body.image 数组

### T1.4 关键帧动画
```bash
py scripts/agnes_video_client.py \
  --capability keyframes \
  --prompt "Smooth cinematic transition between keyframes" \
  --keyframes "https://example.com/frame_a.png,https://example.com/frame_b.png" \
  --duration 10 \
  --output outputs/test/keyframes_test.mp4
```

**预期**：使用 extra_body.mode = keyframes

---

## T2：字幕生成器

### T2.1 英文（默认）
```bash
py scripts/subtitle_manager.py \
  --product-key oil_casing \
  --lang en \
  --out outputs/test/subs_en.json
```

**预期输出**：
```json
{
  "lang": "en",
  "subtitles": [
    {"text": "OCTG Oil Casing", "start": 0.0, "end": 1.5},
    {"text": "API 5CT Certified", "start": 1.5, "end": 3.5},
    {"text": "High Strength Corrosion Resistant", "start": 3.5, "end": 5.5},
    {"text": "Oilfield Drilling Grade", "start": 5.5, "end": 7.5}
  ]
}
```

### T2.2 中文
```bash
py scripts/subtitle_manager.py \
  --product-key oil_casing \
  --lang zh \
  --out outputs/test/subs_zh.json
```

### T2.3 中英双语
```bash
py scripts/subtitle_manager.py \
  --product-key oil_casing \
  --lang bilingual \
  --out outputs/test/subs_bi.json
```

### T2.4 自定义文本
```bash
py scripts/subtitle_manager.py \
  --custom-text "Welcome\nContact us\nVisit website" \
  --duration 9 \
  --out outputs/test/subs_custom.json
```

**预期**：3 条字幕，每条 3 秒

---

## T3：视频拼接

### T3.1 两段拼接（无过渡）
```bash
py scripts/video_postprocess.py \
  --segments outputs/test/i2v_test.mp4 outputs/test/multi_test.mp4 \
  --output outputs/test/concat_test.mp4 \
  --transition none \
  --bgm-style none
```

**预期**：直接拼接，时长 = 段1 + 段2

### T3.2 多段 + 淡入淡出
```bash
py scripts/video_postprocess.py \
  --segments seg1.mp4 seg2.mp4 seg3.mp4 \
  --output outputs/test/xfade_test.mp4 \
  --transition fade \
  --bgm-style corporate
```

**预期**：3 段 xfade 拼接，总时长 - 1 秒（过渡消耗）

---

## T4：BGM 混音

```bash
py scripts/video_postprocess.py \
  --segments outputs/test/i2v_test.mp4 \
  --output outputs/test/bgm_test.mp4 \
  --bgm-style corporate
```

**预期**：
- 输出有 BGM 的 MP4
- 原声音量 10% + BGM 音量 30%
- BGM 自动 loop 到视频时长

**前置**：`assets/bgm/corporate.mp3` 存在；否则降级为无声

---

## T5：字幕烧录

```bash
py scripts/subtitle_manager.py \
  --product-key oil_casing --lang en --out outputs/test/subs_en.json

py scripts/video_postprocess.py \
  --segments outputs/test/i2v_test.mp4 \
  --output outputs/test/subtitled_test.mp4 \
  --bgm-style corporate \
  --subtitles-json outputs/test/subs_en.json \
  --subtitle-lang en
```

**预期**：
- 输出视频底部居中有白色字幕
- 半透明黑底
- 按时间顺序显示 4 条字幕

---

## T6：Prompt 构造器

### T6.1 基础
```bash
echo '{
  "product_name": "石油套管",
  "product_category": "machinery",
  "scene_motion": "orbit",
  "duration": 10,
  "aspect_ratio": "16:9"
}' > entities_test.json

py scripts/prompt_builder.py \
  --entities entities_test.json \
  --out prompt_test.json
```

**预期输出**：
```json
{
  "prompt": "OCTG oil casing pipe, slow 360 degree orbit camera, smooth rotation, studio lighting, cinematic motion, pure white background, professional studio lighting, soft shadows, product photography style",
  "negative_prompt": "fast motion, shaky camera, blur, distortion",
  "capability": "i2v",
  "duration": 10,
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### T6.2 多图I2V
```bash
echo '{
  "product_name": "集装箱",
  "product_category": "equipment",
  "scene_motion": "pull_out",
  "reference_images": ["url1", "url2", "url3"]
}' > entities_multi.json

py scripts/prompt_builder.py --entities entities_multi.json --out prompt_multi.json
```

**预期**：capability 自动切换为 `multi_i2v`

---

## T7：B2B 闭环 Parser

```bash
# 准备：HLZD-B2B工业品调研 目录下有"石油套管B2B市场调研报告.md"
py scripts/b2b_research_parser.py \
  --auto \
  --out b2b_entities_test.json
```

**预期**：
```json
{
  "product_name": "石油套管",
  "hs_code": "730429",
  "product_category": "machinery",
  "target_markets": ["UAE", "Saudi Arabia", "US"],
  "scenes": ["油田", "钻井平台"],
  "source_report": "D:\\xxx\\石油套管B2B市场调研报告.md",
  "reference_images": [{...}],
  "reference_image": "..."
}
```

---

## T8：Orchestrator 全流程

### T8.1 最小调用
```bash
py scripts/orchestrator.py \
  --auto \
  --product-name 石油套管 \
  --duration 15 \
  --bgm-style corporate \
  --subtitle-lang en
```

**预期**：
1. 自动检测 B2B 报告 → 解析产品信息
2. 自动检测图片skill 历史 → 选参考图
3. 调 Agnes 生成 1 段 15s I2V
4. FFmpeg 加 BGM + 英文字幕
5. 输出：`outputs/videos/YYYY-MM-DD/石油套管_HHMMSS.mp4`
6. 历史：`outputs/history/YYYY-MM-DD.json`

### T8.2 批量生成 3 条
```bash
py scripts/orchestrator.py \
  --auto \
  --product-name 阀门 \
  --duration 10 \
  --quantity 3 \
  --aspect-ratio 1:1
```

**预期**：3 个不同时间戳的 MP4 文件

### T8.3 长视频自动拼接
```bash
py scripts/orchestrator.py \
  --auto \
  --product-name 集装箱 \
  --duration 45 \
  --aspect-ratio 16:9
```

**预期**：
- 拆分为 3 段（15s × 3）
- 生成 3 个 seg 文件
- 拼接为 1 个 ~44s 最终 MP4

---

## T9：图片skill 历史检测

**前置**：HLZD-图片生成 已生成产品图到 `outputs/generated/YYYY-MM-DD/`

```bash
py scripts/b2b_research_parser.py \
  --auto \
  --max-images 4 \
  --out entities_with_imgs.json
```

**预期**：`reference_images` 包含 1-4 张最新 PNG 路径

---

## T10：18 秒以上自动拼接

```bash
echo '{
  "product_name": "挖掘机",
  "product_category": "equipment",
  "capability": "i2v",
  "duration": 60,
  "aspect_ratio": "16:9",
  "bgm_style": "industrial",
  "subtitle_lang": "bilingual",
  "reference_image": "https://..."
}' > long_video_entities.json

py scripts/orchestrator.py --entities long_video_entities.json
```

**预期**：
- 拆分为 4 段（15s × 4）
- 4 次 Agnes API 调用
- 1 次 xfade 拼接
- 最终 ~57s MP4

---

## T11：质量优化（管材类·OCTG 案例）

> 详见 `references/quality-optimization.md`

### T11.1 失败案例：orbit + 简单 prompt
```bash
# 触发几何变形 + 错字
py scripts/agnes_video_client.py \
  --capability i2v \
  --prompt "OCTG oil casing pipes rotating 360 degrees on factory floor" \
  --image "https://i.ibb.co/xxx.png" \
  --duration 5 \
  --output outputs/test/quality_bad.mp4
```

**预期问题**：
- ❌ 管子在旋转过程中被压扁（orbit 镜头对 3D 圆柱体理解有偏差）
- ❌ 出现 "OOCTG" 错字（行业缩写被展开）

### T11.2 修复方案：push_in + 强化 prompt + preset 默认值
```bash
# 已沉淀到 preset：直接 --auto 即可
py scripts/orchestrator.py \
  --auto \
  --product-name 石油套管 \
  --capability i2v \
  --duration 5 \
  --aspect-ratio 1:1
```

**预期改进**：
- ✅ push_in 镜头避免 3D 旋转变形
- ✅ preset 默认 negative 包含 "OCTG must be four letters only"
- ✅ 全局 negative 包含 "no text overlay, no labels, no watermarks"
- ✅ 管子保持圆柱形、文字不出现

### T11.3 验证：用同一张图 + 修复后 prompt
```bash
py scripts/agnes_video_client.py \
  --capability i2v \
  --prompt "Five cylindrical round metal OCTG oil casing pipes lying parallel on factory floor, camera slowly pushes in toward the pipe ends, professional industrial cinematography, warm workshop lighting, photorealistic industrial photography" \
  --image "https://i.ibb.co/v4RJSYKJ/b2a5705fe6e6.jpg" \
  --duration 5 \
  --aspect-ratio 1:1 \
  --negative-prompt "blurry, distorted, low quality, watermark, text overlay, flat pipes, square pipes, no text overlay, no labels, no watermarks, OCTG must be four letters only" \
  --output outputs/test/quality_good.mp4
```

**预期**：管子保持圆柱形 + 无错字

### T11.4 质量检查清单

- [ ] 管材类默认 motion = `push_in`（非 orbit）
- [ ] negative_prompt 含 "flat pipes, square pipes"
- [ ] negative_prompt 含 "no text overlay, no labels"
- [ ] 行业缩写产品加 "X must be N letters only" 防护
- [ ] 视频目视检查：管子形状、字样正确性

---

## 验收标准

| 项 | 标准 |
|----|------|
| **功能完整** | T1-T10 全部通过 |
| **代码质量** | 所有 .py 文件无语法错误（`py_compile`） |
| **接口兼容** | 与 HLZD-图片生成 输出结构对齐 |
| **错误处理** | Agnes 4xx/5xx 正确报错 + 重试 |
| **Windows 兼容** | 中文不乱码、路径处理正确 |
| **B2B 闭环** | T7 自动检测报告成功 |
| **图片闭环** | T9 自动检测图片成功 |
| **拼接正确** | T10 长视频拼接无黑场异常 |

---

## 跑测试前置

```bash
# 1. 安装依赖
cd C:\Users\13864\.claude\skills\HLZD-视频生成
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 AGNES_API_KEY=ag-xxx

# 3. 检查 FFmpeg
ffmpeg -version
# 应输出版本信息

# 4. （可选）准备测试 BGM
# 下载免版权 BGM 到 assets/bgm/corporate.mp3

# 5. 创建测试输出目录
mkdir outputs/test
```

---

## 已知测试限制

1. **真实 API 调用**：T1/T8/T10 会真实消耗 Agnes 配额（当前限时免费）
2. **公网图片**：T1.2-T1.4 需要可公网访问的图片 URL
3. **首次运行**：FFmpeg 可能需要编译 libx264（大部分预编译版已包含）
4. **网络环境**：中国大陆访问 agnes-ai.com 可能需要科学上网
5. **生成时间**：单段视频 30-120 秒，批量测试建议安排在空闲时间