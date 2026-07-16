# Agnes Video V2.0 API 参考

> 文档抓取时间：2026-07-06
> 来源：https://agnes-ai.com/zh-Hans/docs/agnes-video-v20

## 概述

Agnes-Video-V2.0 是一款面向生产场景的视频生成模型，支持文生视频、图生视频、多图视频生成以及关键帧动画工作流。开发者可以使用文本提示词、图片 URL 或多张参考图片生成高质量视频。

**适用场景**：故事讲述、营销视频、产品演示、社交媒体内容、应用动态素材、AI 创意工作流。

## API 接口

### 创建视频任务

| 项目 | 说明 |
| --- | --- |
| 接口地址 | `https://apihub.agnes-ai.com/v1/videos` |
| 请求方法 | POST |
| Content-Type | application/json |
| 认证方式 | Bearer Token |

### 获取视频结果（推荐）

| 项目 | 说明 |
| --- | --- |
| 接口地址 | `https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>` |
| 请求方法 | GET |
| 认证方式 | Bearer Token |

## 请求参数

### 必需参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| model | string | 模型名称，固定 `agnes-video-v2.0` |
| prompt | string | 视频内容的文本描述 |

### 可选参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| image | string / array | 图片 URL 或图片 URL 数组（I2V 模式） |
| mode | string | 生成模式，例如 `ti2vid` 或 `keyframes` |
| height | integer | 视频高度，默认 768 |
| width | integer | 视频宽度，默认 1152 |
| num_frames | integer | 视频帧数（必须 ≤ 441，遵循 8n+1 规则） |
| frame_rate | number | 视频帧率（1-60） |
| num_inference_steps | integer | 推理步数 |
| seed | integer | 随机种子，用于可复现 |
| negative_prompt | string | 反向提示词 |
| extra_body.image | array | 多图视频或关键帧模式下的输入图片 URL 数组 |
| extra_body.mode | string | 附加模式设置，例如 `keyframes` |

## 标准分辨率档位

| 档位 | 说明 |
| --- | --- |
| 480p | 标清 |
| 720p | 高清（推荐） |
| 1080p | 全高清 |

## 推荐宽高比

| 宽高比 | 适用场景 |
| --- | --- |
| 16:9 | 横版视频、产品演示、网站展示、YouTube |
| 9:16 | 竖版短视频、移动端优先、TikTok / Reels / Shorts |
| 1:1 | 方形视频、社交信息流、产品展示 |
| 4:3 | 传统横版、通用演示 |
| 3:4 | 竖版演示、肖像、产品为主 |

## 视频时长控制

公式：`seconds = num_frames / frame_rate`

约束：
- `num_frames` ≤ 441
- `num_frames` 遵循 `8n + 1` 规则
- `frame_rate` 范围 1-60

### 常用时长设置

| 目标时长 | 推荐参数 |
| --- | --- |
| 约 3 秒 | num_frames: 81, frame_rate: 24 |
| 约 5 秒 | num_frames: 121, frame_rate: 24 |
| 约 10 秒 | num_frames: 241, frame_rate: 24 |
| 约 18 秒（上限） | num_frames: 441, frame_rate: 24 |

## 创建响应

```json
{
  "id": "task_YOUR_TASK_ID",
  "task_id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "object": "video",
  "model": "agnes-video-v2.0",
  "status": "queued",
  "progress": 0,
  "created_at": 1780457477,
  "seconds": "10.0",
  "size": "1280x768"
}
```

## 任务状态

| 状态 | 说明 |
| --- | --- |
| queued | 任务正在队列中等待 |
| in_progress | 视频正在生成 |
| completed | 视频生成成功 |
| failed | 视频生成失败 |

## 完成响应

```json
{
  "id": "task_xxx",
  "video_id": "video_xxx",
  "model": "agnes-video-v2.0",
  "object": "video",
  "status": "completed",
  "progress": 100,
  "seconds": "10.0",
  "size": "1280x768",
  "remixed_from_video_id": "https://storage.googleapis.com/agnes-aigc/aigc/videos/2026/06/03/video_xxx.mp4",
  "error": null
}
```

## 错误码

| 状态码 | 说明 |
| --- | --- |
| 400 | 请求无效，请检查请求参数 |
| 401 | 未授权，请检查 API Key |
| 404 | 任务或视频未找到 |
| 500 | 服务器错误 |
| 503 | 服务繁忙，请稍后重试 |

## 定价

| 类型 | 标准价格 | 当前价格 |
| --- | --- | --- |
| 视频时长 | $0.005 / 秒 | **$0 / 秒**（限时） |

## 推荐参数

| 场景 | 推荐设置 |
| --- | --- |
| 标准视频生成 | width: 1152, height: 768, num_frames: 121, frame_rate: 24 |
| 社交短视频 | num_frames: 81 或 121, frame_rate: 24 |
| 较长视频 | 增大 num_frames 或降低 frame_rate |
| 更流畅的运动 | frame_rate: 24 或 30 |
| 可复现结果 | 设置固定的 seed |
| 关键帧过渡 | extra_body.mode: "keyframes" |
| 避免不需要的内容 | 使用 negative_prompt |

## 4 种示例

### 1. 文生视频（T2V）

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "A cinematic shot of a cat walking on the beach at sunset, soft ocean waves, warm golden lighting, realistic motion",
    "height": 768,
    "width": 1152,
    "num_frames": 121,
    "frame_rate": 24
  }'
```

### 2. 图生视频（I2V·单图）

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "The woman slowly turns around and looks back at the camera, natural facial expression, cinematic camera movement",
    "image": "https://example.com/image.png",
    "num_frames": 121,
    "frame_rate": 24
  }'
```

### 3. 多图视频生成（多图I2V）

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "Create a smooth transformation scene between the two reference images, cinematic lighting, consistent character identity, natural motion",
    "extra_body": {
      "image": [
        "https://example.com/image1.png",
        "https://example.com/image2.png"
      ]
    },
    "num_frames": 121,
    "frame_rate": 24
  }'
```

### 4. 关键帧动画（keyframes）

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "Generate a smooth cinematic transition between the keyframes, maintaining visual consistency and natural camera movement",
    "extra_body": {
      "image": [
        "https://example.com/keyframe1.png",
        "https://example.com/keyframe2.png"
      ],
      "mode": "keyframes"
    },
    "num_frames": 121,
    "frame_rate": 24
  }'
```

## HLZD-视频生成 skill 的封装策略

本 skill 已将上述 API 完整封装为 `scripts/agnes_video_client.py`，提供：

1. **4 种创建函数**：`create_t2v` / `create_i2v` / `create_multi_image` / `create_keyframes`
2. **统一轮询**：`poll_video_result`（10s/次，5min 超时）
3. **指数退避**：`call_with_retry`（1s, 2s 重试）
4. **Windows 兼容**：UTF-8 包装器
5. **一键式**：`generate_and_download` 创建 + 轮询 + 下载

调用方不需要直接接触 HTTP 细节，只需传入 `capability` + `prompt` + 参考图即可。