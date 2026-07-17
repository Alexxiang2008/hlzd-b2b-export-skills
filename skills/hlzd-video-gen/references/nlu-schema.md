# HLZD-视频生成 - NLU Schema 详解

## 概述

本 skill 的 NLU（自然语言理解）由 Claude 自身承担，无需额外的 NLP 模型。Claude 从用户输入中抽取 17 个实体，然后路由到对应的能力。

## 实体抽取优先级

```
1. B2B 报告解析（最高优先级，闭环输入）
2. HLZD-图片生成 历史图片（参考图自动闭环）
3. 用户显式输入
4. Preset 默认值
5. Skill 通用默认
```

## 完整 Schema

### 基础类

| 实体 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `product_name` | string | ✅ | — | 中文/英文产品名 |
| `product_category` | enum | ✅ | 追问 | machinery/equipment/materials/other |

### 能力类

| 实体 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `capability` | enum | ✅ | i2v | i2v/multi_i2v/keyframes/t2v |
| `reference_images` | path[] | 视 | — | 参考图路径（自动从图片skill 历史读取） |
| `source_image_dir` | path | 自动 | 图片skill outputs | 闭环读取 |

### 视频参数类

| 实体 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `scene_motion` | enum | ❌ | orbit | 见下方枚举 |
| `scene_preset` | enum | ❌ | studio_white | 见下方枚举 |
| `duration` | int | ❌ | 10 | 5-60 秒 |
| `aspect_ratio` | enum | ❌ | 16:9 | 见下方枚举 |
| `resolution` | enum | ❌ | 720p | 480p/720p/1080p |

### 后期类

| 实体 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bgm_style` | enum | ❌ | corporate | none/corporate/industrial/upbeat/epic |
| `subtitle` | bool | ❌ | true | 是否添加字幕 |
| `subtitle_lang` | enum | ❌ | en | zh/en/bilingual |

### 业务类

| 实体 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `target_platform` | enum | ❌ | aliinternational | 见下方枚举 |
| `quantity` | int | ❌ | 1 | 1-4 候选 |
| `target_market` | string | ❌ | null | 影响 BGM/字幕本地化 |
| `source_report` | path | 自动 | null | B2B 报告路径（智能检测） |

## 枚举值

### capability

| 值 | 含义 | Agnes API |
|----|------|-----------|
| `i2v` | 图生视频（单图） | `image: "URL"` |
| `multi_i2v` | 多图生视频 | `extra_body.image: [URL1, URL2]` |
| `keyframes` | 关键帧动画 | `extra_body.image: [...]`, `extra_body.mode: "keyframes"` |
| `t2v` | 文生视频（备用） | 仅 `prompt` |

### scene_motion（参考 `presets/common/motions.yaml`）

| 值 | 含义 | 典型场景 |
|----|------|---------|
| `orbit` | 360° 环绕 | 白底产品展示 |
| `static` | 静态特写 | 产品细节 |
| `push_in` | 镜头推近 | 工艺细节 |
| `pull_out` | 镜头拉远 | 产品全貌 |
| `factory_run` | 工厂运转 | 设备演示 |
| `site_demo` | 工地演示 | 工程机械 |
| `port_logistics` | 港口物流 | 集装箱 |
| `transition` | 镜头切换 | 多段拼接 |
| `installation` | 安装演示 | 装配教程 |
| `material_macro` | 材质微距 | 建材纹理 |

### scene_preset（参考 `presets/common/scenes.yaml`）

| 值 | 含义 |
|----|------|
| `studio_white` | 白底棚拍 |
| `studio_neutral` | 中性灰棚拍 |
| `industrial_workshop` | 工业车间 |
| `outdoor_site` | 户外工地 |
| `port_yard` | 港口堆场 |
| `oil_field` | 油田作业 |
| `warehouse` | 仓储环境 |
| `office_modern` | 现代办公 |

### aspect_ratio

| 值 | 适用场景 |
|----|---------|
| `16:9` | 横版（默认） |
| `9:16` | TikTok/抖音竖版 |
| `1:1` | 阿里国际站主图 |
| `4:3` | 传统横版 |
| `3:4` | 竖版演示 |

### target_platform → 默认参数映射

| 平台 | aspect_ratio | duration | 其它 |
|------|--------------|----------|------|
| `aliinternational` | 1:1 | 10 | 主图视频 |
| `aliinternational-detail` | 16:9 | 30 | 详情页 |
| `tiktok` | 9:16 | 30 | 竖版 |
| `website` | 16:9 | 30 | 官网 |
| `email` | 16:9 | 20 | 邮件附件 |
| `other` | 16:9 | 15 | 通用 |

## 推断规则示例

### 示例 1：用户说"阿里国际站"

```
用户输入："给阀门生成 10 秒阿里国际站主图视频"
↓
推断：
- target_platform = "aliinternational"
- aspect_ratio = "1:1"  （阿里主图默认）
- duration = 10
- product_category = "machinery"  （阀门）
- product_name = "阀门"
```

### 示例 2：用户说"TikTok 短视频"

```
用户输入："给挖掘机做个 TikTok 短视频"
↓
推断：
- target_platform = "tiktok"
- aspect_ratio = "9:16"
- duration = 30  （TikTok 默认时长）
- product_category = "equipment"
- scene_motion = "factory_run"  （挖掘机默认）
- bgm_style = "upbeat"  （TikTok 调性）
```

### 示例 3：用户说"工厂实拍"

```
用户输入："给集装箱做一段工厂实拍演示视频"
↓
推断：
- scene_motion = "factory_run"  （用户关键词"实拍演示"）
- 实际推荐："port_logistics"  （集装箱更合适港口）
- 此处会有追问让用户确认
```

## 矛盾处理

| 矛盾 | 处理 |
|------|------|
| 用户说"白底"但参考图是工厂图 | 主动指出，询问是 I2V（保留背景）还是 T2V（重做白底） |
| 时长 > 60s | 自动截断到 60s，提示用户确认 |
| aspect_ratio 与 target_platform 冲突 | 以 target_platform 为准，提示用户 |
| 无参考图但 capability=i2v | 追问用户提供图片 URL |
| 中英字幕冲突 | 默认英文，提示用户切换 |

## NLU 输出格式

最终输出 `entities.json`：

```json
{
  "product_name": "石油套管",
  "product_category": "machinery",
  "capability": "i2v",
  "scene_motion": "factory_run",
  "scene_preset": "oil_field",
  "duration": 30,
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "target_platform": "aliinternational-detail",
  "bgm_style": "corporate",
  "subtitle": true,
  "subtitle_lang": "en",
  "quantity": 1,
  "target_market": "UAE",
  "reference_image": "https://storage.googleapis.com/.../石油套管_001.png",
  "reference_images": ["https://...png", "https://...png"],
  "source_report": "D:\\AI-P\\skills\\HLZD-B2B工业品调研\\石油套管B2B市场调研报告.md"
}
```