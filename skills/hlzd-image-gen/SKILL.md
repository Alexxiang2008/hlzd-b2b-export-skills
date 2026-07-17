---
name: hlzd-image-gen
description: "B2B 工业品产品图生成 —— 文生图（T2I）/ 图生图（I2I）/ 白底抠图 / 阿里国际站主图 / 批量风格化。Agnes Image 2.1 Flash + rembg。输出 PNG + 历史 JSON。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: content-asset
  triggered_by:
    - 生图
    - 文生图
    - 图生图
    - T2I
    - I2I
    - 产品图
    - 白底图
    - 白底主图
    - 抠图
    - 去背景
    - 工业品配图
    - 阿里国际站主图
    - 机械配图
    - 设备渲染
    - 建材展示
    - 风格迁移
    - 批量生图
    - generate product image
    - remove background
    - product photo
    - industrial product image
---

# hlzd-image-gen — B2B 工业品 AI 生图

> 解决 B2B 工业品（机械/设备/建材）的精准生图问题：白底合规 + 工程精度 + 平台规格。

---

## Quick Commands

```bash
# T2I 文生图（最常用）
hlzd-image-gen "石油套管" "白底棚拍"
hlzd-image-gen "蝶阀 D71X" "45度视角，棚拍光"

# I2I 图生图（风格迁移）
hlzd-image-gen --i2i D:\ref.jpg "保持风格，换成水泥工地背景"

# 抠图（白底图）
hlzd-image-gen --bg-remove D:\product.jpg --output D:\product_white.png

# B2B 闭环（自动检测最新 HLZD-B2B工业品调研 报告）
hlzd-image-gen --auto-b2b --chart-type funnel

# 批量生图（同一报告 3 个市场各 1 张）
hlzd-image-gen --auto-b2b --quantity 3

# CLI 底层调用（如有自定义 entities）
py scripts/orchestrator.py --entities entities.json --capability t2i
```

---

## 定位

| 对比项 | 通用生图工具（MJ/SD Web） | **hlzd-image-gen** |
|---|---|---|
| 适用品类 | 消费品/艺术创作/插画 | **B2B 工业品**（机械/设备/建材）|
| Prompt 风格 | 艺术化形容词 | **行业术语 + 工程精度**（套管/阀门/HS 编码）|
| 一致性 | 每张图独立 | **多角度/多场景保持产品结构一致**|
| 输出尺寸 | 创意比例 | **平台规格**（阿里 1:1、博客 16:9、A+ 1200×628）|
| 合规 | 宽松 | **白底图 + 无 LOGO + 无版权元素**|
| 生态 | 独立工具 | **与 HLZD-B2B工业品调研 + HLZD-D3可视化 全链路打通**|

**核心原则**：B2B 工业品图不是"好看"，是"准确 + 一致 + 合规"。

---

## 核心能力矩阵

| 能力 | 实现 | 适用场景 | 单图耗时 |
|---|---|---|---|
| **T2I**（文生图） | Agnes Image 2.1 Flash | 无参考图，从零生成 | 5-15s |
| **I2I**（图生图） | Agnes Image 2.1 Flash | 有参考图，风格迁移 | 8-20s |
| **抠图** | rembg（U²-Net/ISNet） | 商品图去背景 | 1-3s |

**何时用哪种**：
- 用户说"生成 XX 的图" → T2I
- 用户说"把这张图改成 XX" → I2I
- 用户说"抠图 / 白底图 / 去背景" → 抠图

---

## 数据源

| 数据源 | 用途 | 费用 |
|---|---|---|
| Agnes Image 2.1 Flash | T2I + I2I 云端生图 | 当前 $0/图（促销），标准 $0.003/图 |
| rembg | 本地抠图（U²-Net / ISNet） | 免费 |
| HLZD-B2B工业品调研 | 闭环输入（产品名/HS 编码/目标市场） | 免费 |

### Agnes API 速查

```http
POST https://apihub.agnes-ai.com/v1/images/generations
Authorization: Bearer ${AGNES_API_KEY}
Content-Type: application/json

# T2I 请求体
{
  "model": "agnes-image-2.1-flash",
  "prompt": "...",
  "size": "1024x1024",
  "extra_body": {"response_format": "url"}
}

# I2I 请求体（图生图）
{
  "model": "agnes-image-2.1-flash",
  "prompt": "...",
  "size": "1024x1024",
  "image": ["https://example.com/input.jpg"],
  "extra_body": {"response_format": "url"}
}
```

---

## 工作流（主流程）

```
输入（自然语言或 entities.json）
    ↓
[1] NLU 解析（Claude 自身）→ 追问缺失字段
    ↓
[2] B2B 闭环检测（可选）
    → 扫描 HLZD-B2B工业品调研 目录
    → 按 mtime 取最新报告 → 解析 markdown 补全实体
    ↓
[3] 展示理解回执（Markdown 表格）
    ↓
[4] Prompt Builder
    → 加载 preset（按 product_category）
    → 拼装中英双语 prompt
    ↓
[5] 能力路由 + 提交
    ├─ T2I → agnes_client.generate_t2i()
    ├─ I2I → agnes_client.generate_i2i()
    └─ 抠图 → image_enhancer.remove_bg()
    ↓
[6] 出图 + 历史保存
    → outputs/generated/YYYY-MM-DD/{product}_{seq}.png
    → outputs/history/YYYY-MM-DD.json
    ↓
[7] 展示结果 + 追问迭代
```

### Step 2.5 专业访谈（强推荐）

**何时触发**：用户提到具体工业品（套管/阀门/轴承/钢结构等）且未指定专业规格时。

**Claude 的执行步骤**：
1. 检测到产品名属于工业品类
2. 主动调用 `AskUserQuestion` 工具问关键专业参数（3-5 个）
3. 用户回答后存入 `entities.expert_answers`
4. prompt_builder 自动引用这些参数

**套管访谈模板**（钢级 / 外径 / 扣型 / 端部 / 长度）
**阀门访谈模板**（类型 / 压力等级 / 连接方式 / 阀体材质 / 操作方式）
**钢结构访谈模板**（用途 / 主要构件 / 表面处理 / 防腐等级）

完整工业品规格速查表见 `references/industrial-specs.md`。

---

## 输出格式

```
D:\AI-P\skills\hlzd-image-gen\outputs\
├── generated\
│   └── YYYY-MM-DD\
│       └── {产品名}_{序号}.png
└── history\
    └── YYYY-MM-DD.json
```

### 历史 JSON 字段

```json
{
  "date": "2026-07-06",
  "entries": [{
    "timestamp": "2026-07-06T14:23:15",
    "capability": "t2i",
    "product_name": "石油套管",
    "product_category": "machinery",
    "model": "agnes-image-2.1-flash",
    "params": {"prompt": "...", "size": "1024x1024"},
    "image_url": "https://storage.googleapis.com/agnes-aigc/xxx.png",
    "local_path": "D:\\...\\石油套管_001.png",
    "source_report": "D:\\...\\石油套管B2B市场调研报告.md",
    "cost": 0.0
  }],
  "total_cost": 0.0
}
```

---

## 工业品 Preset 库

详见 `presets/` 目录（6 个 YAML）。

| 文件 | 类别 | 覆盖产品 |
|---|---|---|
| `presets/industrial/machinery.yaml` | 机械类 | 套管/阀门/轴承/工具 |
| `presets/industrial/equipment.yaml` | 设备类 | 集装箱/工程机械/发电机 |
| `presets/industrial/materials.yaml` | 建材类 | 钢结构/铝合金/塑料管 |
| `presets/common/angles.yaml` | 通用视角 | front/45deg/overhead/cutaway/detail |
| `presets/common/lighting.yaml` | 通用光照 | studio/natural/dramatic/softbox |
| `presets/common/styles.yaml` | 通用风格 | photorealistic/catalog/technical/3d-render |

---

## 限制与边界

### ✅ 适合
- B2B 工业品主图、场景图、细节图
- 商品图抠图（白底图、透明 PNG）
- 参考图风格迁移（保持工业质感）
- 与 HLZD-B2B工业品调研 闭环配图

### ❌ 不适合
- 消费品/服装/美妆（风格不匹配）
- 真人照片（合规风险 + Agnes 模型效果差）
- 受版权保护品牌 LOGO（合规问题）
- 图片放大/超分辨率（v0.1 不支持）

### ⚠️ 硬限制
- 单次批量 ≤ 8 张
- 参考图必须可公网访问（I2I）或本地文件路径
- Agnes 单图超时 5 分钟自动重试 2 次
- rembg 仅支持 PNG/JPG/WebP

---

## 错误地图

| 异常 | 触发场景 | 处理 |
|---|---|---|
| `HTTP 401` | token 无效/过期 | 检查 `.env` 中 `AGNES_API_KEY` |
| `HTTP 429` | 限流 | 自动重试 2 次（指数退避）|
| `HTTP 400` | 参数错误 | 检查 prompt 敏感词 + size 合规 |
| 网络超时 | 30s 无响应 | 自动重试 2 次 |
| rembg 模型未找到 | 首次运行 | 联网自动下载 ~170MB U²-Net |
| B2B 报告未找到 | 智能检测失败 | 用户显式提供路径 |
| Windows python Exit 49 | Store 劫持 | 用 `py` launcher |

---

## 依赖与部署

```bash
# 1. 安装依赖
py -m pip install -r requirements.txt

# 2. 配置 .env
copy .env.example .env
# 编辑 .env，填入 AGNES_API_KEY=your_key

# 3. rembg 首次运行需联网下载模型（约 170MB）
# 模型路径：%USERPROFILE%\.u2net\u2netp.onnx

# 4. Panmira 安装（bot 启用）
mb skills install hlzd-image-gen 青囊
```

> **Windows 上 `python` 可能被劫持到 Windows Store**，统一使用 `py` launcher。

---

## 验证清单

新版本发布前必跑：
- [ ] `mb skills list` 看到 `hlzd-image-gen`
- [ ] 飞书发"生成石油套管白底图" → logs 看到 selected
- [ ] T2I 单图测试（5-15s 出图）
- [ ] I2I 风格迁移（带参考图 URL）
- [ ] 抠图（rembg 测试）
- [ ] B2B 闭环：自动检测最新报告 → 补全实体 → 生图
- [ ] 历史 JSON 写入成功（含 9 字段）
- [ ] 错误地图覆盖所有异常分支

---

## 自动串联

### 上游（被谁触发）
- **HLZD-B2B工业品调研**：报告生成后自动调用本 skill 出产品配图
- **HLZD-email-group**：邮件需要配图时调用本 skill

### 下游（触发谁）
- 生图后 → 可调 HLZD-D3可视化 嵌入 dashboard
- 生图后 → 可调 HLZD-办公文档 嵌入抬头报价单
- 生图后 → 可调 HLZD-视频生成 做图生视频

### 被动串联
- 历史 JSON 每日统计 + 报表

---

## 已知限制（v0.1 接受）

- Agnes 仅一个模型（`agnes-image-2.1-flash`），无降级链
- 不支持实时图片放大/超分辨率
- 不支持参考图批量混合（一次只能 1 张参考图）

---

## 后续路线（v0.2+）

| 版本 | 新增 |
|---|---|
| v0.2 | 接入通义万相 / Stable Diffusion 作为降级链 |
| v0.2 | 图片放大（Real-ESRGAN）|
| v0.3 | 视频首帧生成（与 HLZD-视频生成 深度协同）|
| v0.3 | 阿里国际站 API 直传（自动上架）|
| v0.4 | 多参考图风格混合 |