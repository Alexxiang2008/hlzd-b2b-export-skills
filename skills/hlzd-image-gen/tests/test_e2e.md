# HLZD-图片生成 - E2E 测试用例

本文件包含 5 条 E2E 测试用例，覆盖生图 skill 的所有核心能力。

## 测试前置

### 环境准备

```bash
# 1. 安装依赖（首次）
cd "D:\AI-P\skills\HLZD-图片生成"
pip install -r requirements.txt

# 2. 配置 .env
copy .env.example .env
# 编辑 .env，填入 AGNES_API_KEY=your_real_key

# 3. 验证依赖
py -c "import requests, yaml, PIL; print('基础依赖 OK')"
py -c "import rembg; print('rembg OK')"
```

### 同步到扫描目录

```bash
# 复制 SKILL.md + scripts/ + presets/ + references/ 到扫描目录
# 注意：outputs/ 不复制
xcopy /E /I /Y "D:\AI-P\skills\HLZD-图片生成\scripts" "C:\Users\13864\.claude\skills\HLZD-图片生成\scripts"
xcopy /E /I /Y "D:\AI-P\skills\HLZD-图片生成\presets" "C:\Users\13864\.claude\skills\HLZD-图片生成\presets"
xcopy /E /I /Y "D:\AI-P\skills\HLZD-图片生成\references" "C:\Users\13864\.claude\skills\HLZD-图片生成\references"
copy /Y "D:\AI-P\skills\HLZD-图片生成\SKILL.md" "C:\Users\13864\.claude\skills\HLZD-图片生成\SKILL.md"
```

---

## 测试 1：环境就绪（验证脚本可执行）

```bash
# 6 个脚本的 --help 都应成功退出（退出码 0）
py scripts/agnes_client.py --help
py scripts/prompt_builder.py --help
py scripts/b2b_research_parser.py --help
py scripts/image_enhancer.py remove-bg --help
py scripts/output_manager.py --help
py scripts/orchestrator.py --help
```

**通过标准**：6 个脚本全部输出 usage 文档，退出码 0。

**手动验证**：
```bash
# B2B 智能检测（应能找到已有的报告或返回警告）
py scripts/b2b_research_parser.py --detect-latest

# 提示无报告时的输出：
# [警告] 在候选目录中未找到 B2B 市场调研报告
# 这是预期行为，不算失败
```

---

## 测试 2：单图 T2I（端到端，模拟 SKILL.md 工作流）

**场景**：用户说"给石油套管生成一张阿里国际站白底主图"

**工作流模拟**：
1. Claude 解析自然语言 → entities
2. orchestrator 调用 prompt_builder + agnes_client + output_manager

### 步骤 2.1：构造 entities.json

```bash
cat > entities.json << 'EOF'
{
  "product_name": "石油套管",
  "product_category": "machinery",
  "capability": "t2i",
  "scene": "white background product shot, commercial catalog style",
  "angle": "45deg",
  "lighting": "studio",
  "style": "catalog",
  "size": "1024x1024",
  "quantity": 1
}
EOF
```

### 步骤 2.2：单独测试 prompt_builder

```bash
py scripts/prompt_builder.py --entities entities.json --out prompt.json
cat prompt.json
```

**预期输出**：
```json
{
  "prompt": "OCTG oil casing pipe, 45-degree three-quarter angle..., professional studio lighting..., clean catalog product photo..., white background product shot...",
  "negative_prompt": "clutter, people, hands, text, watermark...",
  "model": "agnes-image-2.1-flash",
  "size": "1024x1024",
  "quantity": 1
}
```

### 步骤 2.3：单独测试 agnes_client

```bash
py scripts/agnes_client.py --prompt "OCTG oil casing pipe on white background, 45-degree angle, studio lighting" --size 1024x1024 --output test_output.png
```

**通过标准**：
- `test_output.png` 文件存在且 > 0 字节
- HTTP 200，无错误
- 退出码 0

### 步骤 2.4：完整 orchestrator 调用

```bash
py scripts/orchestrator.py --entities entities.json --capability t2i
```

**通过标准**：
- `outputs/generated/{今日}/石油套管_001.png` 文件存在且 > 0 字节
- `outputs/history/{今日}.json` 含 1 条 entry，含 9 个核心字段（timestamp/capability/product_name/product_category/model/params/image_url/local_path/source_report/cost）
- 退出码 0

---

## 测试 3：I2I 风格迁移

**场景**：用户说"把这张工厂背景的阀门图改成白底"

**注意**：I2I 需要参考图是公网 URL（Agnes API 要求）。本地文件需要先上传到图床。

### 步骤 3.1：准备参考图 URL

手动将测试图（如 `D:\test\valve.jpg`）上传到：
- https://imgur.com/upload
- https://sm.ms/
- 公司 OSS

获取公网 URL，例如：`https://i.imgur.com/abc123.jpg`

### 步骤 3.2：构造 entities

```bash
cat > i2i_entities.json << 'EOF'
{
  "product_name": "阀门",
  "product_category": "machinery",
  "capability": "i2i",
  "scene": "white background, industrial product photo",
  "size": "1024x1024"
}
EOF
```

### 步骤 3.3：调用 orchestrator

```bash
py scripts/orchestrator.py --entities i2i_entities.json --capability i2i --reference "https://i.imgur.com/abc123.jpg"
```

**通过标准**：
- `outputs/generated/{今日}/阀门_i2i_*.png` 文件存在且 > 0 字节
- 生成的图主体与参考图近似，背景变白
- 历史 JSON 含 capability="i2i", params.reference=URL
- 退出码 0

---

## 测试 4：rembg 抠图（白底图）

**场景**：用户说"把产品从背景里抠出来做白底图"

### 步骤 4.1：准备测试图

任意本地 jpg/png 即可（如 `D:\test\valve.jpg`）。

### 步骤 4.2：纯抠图（透明 PNG）

```bash
py scripts/image_enhancer.py remove-bg --input "D:\test\valve.jpg" --output "D:\test\valve_no_bg.png"
```

**首次运行会下载 rembg 模型**：
```
[rembg] 加载模型: u2netp（首次运行需联网下载 ~170MB）
[rembg] 抠图中: D:\test\valve.jpg
[完成] 抠图: D:\test\valve_no_bg.png
```

**通过标准**：
- 输出 PNG 文件 > 0 字节
- 主体保留，背景透明（用图片查看器验证）

### 步骤 4.3：抠图 + 换白底

```bash
py scripts/image_enhancer.py change-bg --input "D:\test\valve.jpg" --bg-color "#ffffff" --output "D:\test\valve_white.png"
```

**通过标准**：
- 输出 PNG 文件 > 0 字节
- 主体保留，背景为纯白（RGB 255,255,255）

### 步骤 4.4：通过 orchestrator 调用（自动归档到 outputs/）

```bash
py scripts/orchestrator.py --capability remove_bg --input "D:\test\valve.jpg"
```

**通过标准**：
- 输出文件保存到 `outputs/generated/{今日}/valve_no_bg.png`
- 历史 JSON 包含 capability="remove_bg"
- 退出码 0

---

## 测试 5：B2B 闭环全链路

**场景**：HLZD-B2B工业品调研 已生成某产品报告，本 skill 自动检测并配图

### 步骤 5.0：前置 - 生成 B2B 报告

如果 HLZD-B2B工业品调研 已有报告（如 `石油套管B2B市场调研报告.md`），跳过此步。

否则先用 HLZD-B2B工业品调研 生成一份：
```bash
py "D:\AI-P\skills\HLZD-B2B工业品调研\scripts\hs_lookup.py" -k "石油套管" --output hs.json
py "D:\AI-P\skills\HLZD-B2B工业品调研\scripts\trade_data.py" --hs 730429 --reporter world --period 2023
# 然后按 SKILL.md 工作流生成 markdown 报告
```

### 步骤 5.1：智能检测 + 解析

```bash
py scripts/b2b_research_parser.py --auto --out b2b_entities.json
```

**预期输出**：
```json
{
  "product_name": "石油套管",
  "hs_code": "730429",
  "product_category": "machinery",
  "target_markets": ["阿联酋", "沙特", ...],
  "scenes": ["油田", "钻井平台", ...],
  "source_report": "D:\\AI-P\\skills\\HLZD-B2B工业品调研\\石油套管B2B市场调研报告.md"
}
```

**通过标准**：5 个核心字段全部非空。

### 步骤 5.2：用 B2B 解析结果生图

```bash
py scripts/orchestrator.py --entities b2b_entities.json --capability t2i
```

**通过标准**：
- 生成的图与 `b2b_entities.json` 中的 `product_name` 匹配（人工肉眼看）
- 历史 JSON 的 `source_report` 字段记录报告路径
- 退出码 0

### 步骤 5.3：一键闭环（--auto-b2b）

```bash
py scripts/orchestrator.py --auto-b2b --capability t2i
```

**通过标准**：与步骤 5.2 一致，且自动从 B2B 报告解析 entities（无需手动指定）。

---

## 验收对照表

| 测试 | 覆盖能力 | 关键验证点 |
|------|---------|----------|
| 1 | 环境就绪 | 6 脚本 --help 退出码 0 |
| 2 | T2I 单图 | 端到端：entities → prompt → agnes → 保存 → 历史 |
| 3 | I2I 风格迁移 | 参考图 URL 输入，输出图与参考图风格近似 |
| 4 | rembg 抠图 | 本地抠图 + 换白底，输出透明或白底 PNG |
| 5 | B2B 闭环 | 智能检测最新报告 + 解析 5 字段 + 生图 |

**全部通过 = MVP 验收达标。**

---

## 故障排查速查

| 现象 | 原因 | 解决 |
|------|------|------|
| `python` 命令报 Exit code 49 | Windows Store 劫持 | 改用 `py` launcher |
| 中文输出乱码 | GBK 编码 | 脚本已内置 UTF-8 wrapper，无需处理 |
| `AGNES_API_KEY` 未设置 | .env 未配置 | 复制 `.env.example` 为 `.env` 并填入真实 key |
| Agnes HTTP 401 | token 无效 | 检查 .env 中 AGNES_API_KEY 是否正确 |
| rembg 首次报"model not found" | 模型未下载 | 联网重试，rembg 会自动下载 ~170MB 模型 |
| B2B 报告未找到 | 目录路径不匹配 | 检查 `b2b_research_parser.py` 中 `DEFAULT_CANDIDATE_DIRS` 配置 |
| 历史 JSON 无 source_report 字段 | 不是 B2B 闭环调用 | 正常，仅 B2B 闭环调用会写入该字段 |

---

## 进阶测试（可选）

### 批量 T2I（4 张）

```bash
cat > batch_entities.json << 'EOF'
{
  "product_name": "阀门",
  "product_category": "machinery",
  "capability": "t2i",
  "quantity": 4,
  "scene": "industrial product showcase"
}
EOF

py scripts/orchestrator.py --entities batch_entities.json --capability t2i
```

**通过标准**：4 张 PNG 文件生成，历史 JSON 含 4 条 entry。

### 自定义尺寸

```bash
cat > custom_size_entities.json << 'EOF'
{
  "product_name": "钢结构",
  "product_category": "materials",
  "capability": "t2i",
  "size": "1024x768"
}
EOF

py scripts/orchestrator.py --entities custom_size_entities.json --capability t2i
```

**通过标准**：输出 PNG 尺寸为 1024×768（用图片查看器验证）。