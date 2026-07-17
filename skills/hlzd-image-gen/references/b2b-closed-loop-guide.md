# 与 HLZD-B2B工业品调研 闭环调用指南

## 1. 闭环架构

```
┌──────────────────────────┐
│ HLZD-B2B工业品调研        │
│ (上游：数据采集)           │
│                          │
│ 输出：markdown 报告       │
│ D:\AI-P\skills\HLZD-    │
│ B2B工业品调研\           │
│ {产品名}B2B市场调研报告.md│
└──────────┬───────────────┘
           │
           │ 智能检测最新报告（按 mtime）
           │ 或用户显式提供路径
           ↓
┌──────────────────────────┐
│ b2b_research_parser.py   │
│ - 解析 markdown          │
│ - 提取 5 字段             │
└──────────┬───────────────┘
           │
           │ 输出 entities.json
           ↓
┌──────────────────────────┐
│ HLZD-图片生成            │
│ (下游：图片生成)          │
│                          │
│ 输入：entities.json      │
│ 输出：PNG 图片 + JSON 历史│
└──────────────────────────┘
```

## 2. 闭环调用方式

### 2.1 智能检测（推荐）

```bash
# 1. 智能检测最新报告 + 解析为 entities
py scripts/b2b_research_parser.py --auto --out b2b_entities.json

# 2. 用 entities 生图
py scripts/orchestrator.py --entities b2b_entities.json --capability t2i
```

智能检测逻辑：
1. 扫描候选目录（按顺序）：
   - `D:\AI-P\skills\HLZD-B2B工业品调研\`
   - `C:\Users\13864\.claude\skills\HLZD-B2B工业品调研\`
   - 用户 `--working-dir` 参数指定的目录
2. 列出所有 `*B2B市场调研报告.md` 文件
3. 按 mtime 倒序，取最新一份
4. 解析 markdown 提取 5 字段
5. 输出 entities.json

### 2.2 用户显式指定报告

```bash
# 用户提供完整路径
py scripts/b2b_research_parser.py --report "D:\AI-P\skills\HLZD-B2B工业品调研\石油套管B2B市场调研报告.md" --out entities.json
py scripts/orchestrator.py --entities entities.json --capability t2i
```

## 3. 解析字段约定

### 3.1 markdown 报告结构（HLZD-B2B工业品调研 输出）

```markdown
# 石油套管 B2B市场调研报告

## 一、HS编码确认
HS编码：730429
...

## 二、市场规模（UN Comtrade 2023）
阿联酋（UAE）进口：$XXX
沙特（Saudi Arabia）进口：$XXX
...

## 三、需求热度（Google Trends）
...

## 四、买家画像与线索
- 矿业/油田营地：xxx
- EPC/总包：xxx
...

## 五、市场机会矩阵
...

## 六、关键词策略
...

## 七、综合建议
...
```

### 3.2 解析提取的 5 字段

| 字段 | 来源 | 正则/规则 |
|------|------|-----------|
| `product_name` | `# {产品名} B2B` 标题 | `^# (.+?) B2B` |
| `hs_code` | `HS编码：730429` | `HS\s*编码[：:]\s*(\d{6})` |
| `product_category` | 全文关键词匹配 | 套管→machinery、集装箱→equipment、钢结构→materials |
| `target_markets` | 市场规模段落加粗国名 | `\*\*([一-龥]+(?:国|酋长国|王国)?)\*\*` |
| `scenes` | 买家画像段场景关键词 | 油田/工地/工厂/车间/矿山/港口/营地 |

## 4. 闭环使用示例

### 示例 1：T2I 文生图（基于调研报告）

```bash
# 用户： 给我刚调研的石油套管配 3 张阿里国际站主图

# 工作流：
# 1. 智能检测最新报告 → 石油套管B2B市场调研报告.md
# 2. 解析 → product_name=石油套管, hs_code=730429, category=machinery, target_markets=[UAE, Saudi Arabia, Nigeria], scenes=[油田, 钻井平台]
# 3. Claude 自动补全：scene=白底棚拍, size=1024x1024, quantity=3
# 4. 展示理解回执（带 B2B 报告引用）
# 5. 用户确认 → orchestrator.py 调用 3 次 agnes_client.generate_t2i()
# 6. 输出：3 张 PNG + 1 条历史 JSON（source_report 字段记录报告路径）
```

### 示例 2：I2I 风格迁移（基于已有产品图）

```bash
# 用户： 把这张工厂背景的阀门图（D:\test\valve.jpg）改成白底主图

# 工作流：
# 1. NLU 解析：capability=i2i, product_name=阀门, reference_image=D:\test\valve.jpg
# 2. 智能检测（可选）：若 report 存在则补全 hs_code
# 3. 展示理解回执（含参考图提示）
# 4. 用户确认 → orchestrator.py 调 agnes_client.generate_i2i()
# 5. Agnes 把 D:\test\valve.jpg 上传到公网（自动），生成白底图
# 6. 输出：1 张 PNG
```

### 示例 3：批量场景图（多市场多场景）

```bash
# 用户： 给石油套管生成 3 张图，分别适配 UAE / Saudi Arabia / 美国市场

# 工作流：
# 1. 智能检测 → 解析报告 → target_markets=[UAE, Saudi Arabia, US]
# 2. Claude 拆分：quantity=3，每个对应一个市场
# 3. 为每个市场定制 scene：
#    - UAE：沙漠油田背景（warm color tone, oil rig visible）
#    - Saudi Arabia：沙漠 + 钻井平台
#    - US：现代化工厂车间
# 4. 展示理解回执（表格列出每张图的参数）
# 5. 用户确认 → 批量生图
# 6. 输出：3 张 PNG + 1 条历史 JSON（含 3 个 entry，每个含 target_market）
```

## 5. 历史 JSON 的 source_report 字段

闭环调用时，历史 JSON 必须包含 `source_report` 字段，记录报告路径：

```json
{
  "entries": [
    {
      "timestamp": "2026-07-06T14:23:15",
      "capability": "t2i",
      "product_name": "石油套管",
      "product_category": "machinery",
      "model": "agnes-image-2.1-flash",
      "params": {
        "prompt": "OCTG oil casing, white background...",
        "size": "1024x1024"
      },
      "image_url": "https://storage.googleapis.com/agnes-aigc/xxx.png",
      "local_path": "D:\\AI-P\\skills\\HLZD-图片生成\\outputs\\generated\\2026-07-06\\石油套管_001.png",
      "source_report": "D:\\AI-P\\skills\\HLZD-B2B工业品调研\\石油套管B2B市场调研报告.md",
      "cost": 0.0
    }
  ]
}
```

`source_report` 字段让历史记录**可追溯**：未来可以反查某张产品图是基于哪份调研报告生成的。

## 6. 失败处理

### 6.1 智能检测未找到报告

→ 提示用户：
> "未找到 HLZD-B2B工业品调研 报告。请：
> A. 先用 HLZD-B2B工业品调研 生成报告
> B. 提供报告完整路径
> C. 不使用 B2B 闭环，纯文字生图"

### 6.2 解析字段缺失（如 hs_code 未匹配到）

→ orchestrator 检测到关键字段缺失时，自动调用 NLU 追问用户补全：
> "从报告未识别到 HS 编码，请手动提供（6 位数字，如 730429）"

### 6.3 报告格式漂移

→ 宽松正则匹配，关键字段返回 `None` 而非抛错。
→ 用户可手动覆盖（Claude 提示用户确认）。

## 7. 与其他 HLZD skills 的协同

```
HLZD-B2B工业品调研   →  报告（产品/HS/市场/买家）
        ↓
HLZD-图片生成        →  产品图（基于报告数据）
        ↓
HLZD-email-group    →  邮件（含产品图作为附件）
```

完整工作流：
1. HLZD-B2B工业品调研 输出报告
2. HLZD-图片生成 读取报告 + 生图
3. HLZD-email-group 读取产品图 + 生成开发邮件