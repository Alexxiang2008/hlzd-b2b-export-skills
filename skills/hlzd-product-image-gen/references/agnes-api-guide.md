# Agnes API 集成指南

> 来源：https://agnes-ai.com/zh-Hans/docs/agnes-image-21-flash
> 抓取时间：2026-07-06

## 1. 概述

Agnes Image 2.1 Flash 是升级版图像生成模型，优化高信息密度图像生成，并支持文生图与图生图工作流。

## 2. 核心能力

- ✅ T2I（文生图）：文本 prompt → 图像
- ✅ I2I（图生图）：文本 prompt + 输入图 → 新图像（支持转换、重绘、风格化编辑）
- ✅ 输出格式：URL 或 Base64
- ❌ 抠图（不支持，需用 rembg 本地库补齐）
- ❌ 放大/超分辨率（不支持，未来扩展）

## 3. API Reference

### 3.1 Endpoint

```
POST https://apihub.agnes-ai.com/v1/images/generations
```

### 3.2 请求头

```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### 3.3 请求参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `model` | string | 是 | 模型名称，使用 `agnes-image-2.1-flash` |
| `prompt` | string | 是 | 图像生成或图像编辑的文本指令 |
| `size` | string | 是 | 输出图像尺寸，例如 `1024x768`、`1024x1024`、`768x1024` |
| `image` | string[] | 图生图必填 | 输入图像数组，支持公共图像 URL 或 Data URI Base64 |
| `return_base64` | boolean | 否 | 文生图需要以 Base64 返回时使用 |
| `extra_body` | object | 否 | 高级工作流的附加参数 |
| `extra_body.response_format` | string | 否 | 输出格式，常见值为 `url` 或 `b64_json` |

## 4. 请求示例

### 4.1 文生图（URL 输出）

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "A clean product photo of an industrial valve on a white studio background",
    "size": "1024x1024",
    "extra_body": {
      "response_format": "url"
    }
  }'
```

### 4.2 图生图（URL 输出）

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Transform to white background, preserve product details",
    "size": "1024x1024",
    "image": ["https://example.com/input-image.png"],
    "extra_body": {
      "response_format": "url"
    }
  }'
```

### 4.3 图生图（Base64 输入 + Base64 输出）

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Make the object matte black while preserving the original composition",
    "size": "1024x1024",
    "image": ["data:image/png;base64,BASE64_HERE"],
    "extra_body": {
      "response_format": "b64_json"
    }
  }'
```

## 5. 响应格式

### 5.1 URL 输出

```json
{
  "created": 1780000000,
  "data": [
    {
      "url": "https://storage.googleapis.com/agnes-aigc/xxx.png",
      "b64_json": null,
      "revised_prompt": null
    }
  ]
}
```

### 5.2 Base64 输出

```json
{
  "created": 1780000000,
  "data": [
    {
      "url": null,
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA...",
      "revised_prompt": null
    }
  ]
}
```

## 6. 定价

| 类型 | 标准价格 | 当前价格（促销） |
| --- | --- | --- |
| 生成图像 | $0.003 / 张 | **$0 / 张** |

> 关注官方公告，促销结束后将恢复标准价格。

## 7. 错误码

| HTTP 状态码 | 含义 | 处理方式 |
|------------|------|---------|
| 200 | 成功 | 解析 `data[0].url` 或 `data[0].b64_json` |
| 400 | 参数错误 | 检查 model/prompt/size 是否合规 |
| 401 | 未授权 | 检查 `AGNES_API_KEY` 是否正确 |
| 429 | 限流 | 重试 2 次（指数退避） |
| 500/503 | 服务异常 | 重试 2 次 |

## 8. 接入检查清单

- [ ] 已注册 Agnes 账号并获取 API Key
- [ ] API Key 已写入 `.env` 文件
- [ ] 网络可达 `apihub.agnes-ai.com`
- [ ] Python 环境已安装 `requests>=2.31.0`
- [ ] 测试 T2I 单图调用成功
- [ ] 测试 I2I（带参考图 URL）调用成功

## 9. 参考链接

- 官方文档：https://agnes-ai.com/zh-Hans/docs/agnes-image-21-flash
- API Hub：https://apihub.agnes-ai.com