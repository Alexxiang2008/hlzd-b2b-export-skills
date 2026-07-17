# NLU Schema 详解

本文件是 SKILL.md 中 NLU 解析部分的详细参考，Claude 在执行实体抽取时应参照本文件。

## 1. 实体抽取 Schema（完整版）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "product_name": {
      "type": "string",
      "description": "产品名（中英文均可）"
    },
    "product_category": {
      "type": "string",
      "enum": ["machinery", "equipment", "materials", "other"],
      "description": "产品类别"
    },
    "capability": {
      "type": "string",
      "enum": ["t2i", "i2i", "remove_bg"],
      "description": "需要的能力"
    },
    "scene": {
      "type": "string",
      "description": "应用场景描述（如：白底棚拍、工厂车间、户外工地）"
    },
    "angle": {
      "type": "string",
      "enum": ["front", "45deg", "overhead", "cutaway", "detail"],
      "description": "视角"
    },
    "lighting": {
      "type": "string",
      "enum": ["studio", "natural", "dramatic", "softbox"],
      "description": "光照"
    },
    "style": {
      "type": "string",
      "enum": ["photorealistic", "catalog", "technical", "3d-render"],
      "description": "视觉风格"
    },
    "size": {
      "type": "string",
      "pattern": "^\\d{3,4}x\\d{3,4}$",
      "description": "Agnes 支持的尺寸（1024x1024 / 1024x768 / 768x1024）"
    },
    "quantity": {
      "type": "integer",
      "minimum": 1,
      "maximum": 8,
      "description": "批量生图数量"
    },
    "reference_image": {
      "type": ["string", "null"],
      "description": "参考图路径或公网 URL（I2I/抠图必填）"
    },
    "target_market": {
      "type": ["string", "null"],
      "description": "目标海外市场（影响场景本地化）"
    },
    "source_report": {
      "type": ["string", "null"],
      "description": "关联的 B2B 调研报告路径"
    },
    "preset_id": {
      "type": "string",
      "description": "选中的 preset ID（Claude 自动按 product_category 推断）"
    }
  },
  "required": ["product_name", "product_category", "capability"]
}
```

## 2. 必填字段的追问优先级

### P0：必须追问（缺一不可）

| 字段 | 追问模板 |
|------|---------|
| `product_name` | 追问产品类别以辅助推断产品名 |
| `product_category` | 【追问 1】 |
| `capability` | 【追问 2】 |

### P1：默认填充，不追问

| 字段 | 默认值 |
|------|--------|
| `scene` | "白底棚拍" |
| `angle` | "45deg" |
| `lighting` | "studio" |
| `style` | "catalog" |
| `size` | "1024x1024" |
| `quantity` | 1 |

### P2：可选，仅在用户明示时设置

| 字段 | 触发条件 |
|------|---------|
| `reference_image` | 用户提供了图片路径/URL，或选了【追问 7】的 B/C |
| `target_market` | 用户明示了海外市场 |
| `source_report` | 智能检测或用户显式提供 |

## 3. 追问决策树

```
用户输入
    ↓
[检查] product_name + product_category + capability 是否齐全？
    ├─ 是 → 继续
    └─ 否 → 按优先级追问
            ↓
       [检查] 是否触发智能 B2B 检测？
            ├─ 用户提到"调研报告"/"刚调研的"/具体报告路径
            │  → 触发 b2b_research_parser
            │  → 解析后补全缺失字段
            │  → 仍有缺失 → 追问
            └─ 用户未提到 → 不触发
                    ↓
                 仅追问 P0 必填字段
```

## 4. 实体推断规则

### 4.1 product_category 推断

| 关键词 | 类别 |
|--------|------|
| 套管/钻探/阀门/轴承/泵/齿轮/油管/法兰/压缩机 | machinery |
| 集装箱/工程机械/发电机/产线/设备/成套 | equipment |
| 钢/铝/混凝土/塑料/建材/管材/型材 | materials |
| 其他未知 | other |

### 4.2 capability 推断

| 关键词 | capability |
|--------|------------|
| 生成/做一个/出一张/配图/画一张 | t2i |
| 改成/换成/参考这张/风格迁移/把XX换成 | i2i |
| 抠图/白底/去背景/透明 | remove_bg |

### 4.3 scene 推断

| 关键词 | scene |
|--------|-------|
| 阿里/白底/主图 | "white background product shot" |
| 官网/画册/场景 | "professional product scene" |
| 展会/海报/营销 | "trade show poster style" |
| 邮件/客户开发 | "professional B2B email attachment" |

### 4.4 size 推断

| 关键词 | size |
|--------|------|
| 阿里主图/正方形/1:1 | 1024x1024 |
| 博客横图/16:9/横幅 | 1024x768 |
| 手机/竖图/3:4 | 768x1024 |

## 5. 矛盾检测

### 5.1 场景与参考图矛盾

用户说"白底图"但 reference_image 是工厂背景图：

→ 主动指出矛盾：
> "您要求白底图，但参考图是工厂背景。请确认：
> A. 用 I2I 风格迁移，把参考图改成白底（保留产品）
> B. 用 T2I，忽略参考图，直接生成白底产品图
> C. 用 remove_bg 抠图，参考图作为输入输出透明 PNG"

### 5.2 capability 与 NLU 推断矛盾

用户说"抠图"但 entities 中 product_name 是新词（无参考图）：

→ 主动追问参考图路径：
> "抠图需要参考图作为输入，请提供图片路径（本地或 URL）"

### 5.3 quantity 与成本矛盾

用户说"生成 20 张"：

→ 主动警告：
> "单次批量 ≤ 8 张，请分批：先生成 8 张，确认后再继续？"

## 6. 回执展示规则

每次生图/抠图前必须展示理解回执（Markdown 表格）。

**回执字段顺序**（从上到下）：
1. capability（最重要）
2. product_name
3. product_category
4. scene / angle / lighting / style / size / quantity
5. reference_image
6. source_report / hs_code / target_market（如果有 B2B 报告）
7. model / 预估成本 / 预估时长

**回执结尾**：
```
确认后回复 "确认" 或 "开始"。
如需修改，请直接说"改成 XX"。
```