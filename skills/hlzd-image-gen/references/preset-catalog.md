# Preset 速查表

本文件是 `presets/` 目录下所有 YAML 文件的可读版速查表。实际数据以 YAML 文件为准。

## 1. 工业品 Preset

### 1.1 machinery（机械类）

| 产品 key | 中文名 | 英文名 | 推荐场景 | 默认视角 | 默认风格 |
|---------|--------|--------|---------|---------|---------|
| `casing` | 石油套管 | OCTG oil casing | 油田/钻井平台 | 45deg | catalog |
| `valve` | 阀门 | industrial valve | 工厂车间/管道系统 | detail | technical |
| `bearing` | 轴承 | bearing | 工厂车间/拆解展示 | cutaway | technical |
| `tool` | 工具 | hand tool / power tool | 车间/作业现场 | 45deg | catalog |

### 1.2 equipment（设备类）

| 产品 key | 中文名 | 英文名 | 推荐场景 | 默认视角 | 默认风格 |
|---------|--------|--------|---------|---------|---------|
| `container_house` | 集装箱房屋 | container house | 建筑工地/营地 | 45deg | photorealistic |
| `generator` | 发电机 | diesel generator | 工厂/机房/工地 | 45deg | catalog |
| `construction_machinery` | 工程机械 | construction machinery | 工地/施工现场 | 45deg | catalog |
| `production_line` | 成套产线 | production line | 工厂车间/展览 | overhead | 3d-render |

### 1.3 materials（建材类）

| 产品 key | 中文名 | 英文名 | 推荐场景 | 默认视角 | 默认风格 |
|---------|--------|--------|---------|---------|---------|
| `steel_structure` | 钢结构 | steel structure | 建筑工地/厂房 | overhead | 3d-render |
| `aluminum_profile` | 铝合金型材 | aluminum profile | 工厂车间/样品 | detail | catalog |
| `steel_pipe` | 钢管 | steel pipe | 工地/管道工程 | 45deg | catalog |
| `plastic_pipe` | 塑料管 | plastic pipe | 工厂车间/管道工程 | detail | catalog |

## 2. 通用 Preset

### 2.1 angles（视角选项）

| key | 中文名 | 英文名 | prompt_en 摘要 |
|-----|--------|--------|---------------|
| `front` | 正面平铺 | front view | dead-on angle, flat composition |
| `45deg` | 45 度立体 | 45-degree angle | three-quarter angle, dimensional |
| `overhead` | 俯视鸟瞰 | overhead | top-down bird's eye view |
| `cutaway` | 剖面展示 | cutaway view | cutaway section, internal structure |
| `detail` | 局部细节 | macro detail | extreme close-up macro detail |

### 2.2 lighting（光照选项）

| key | 中文名 | 英文名 | prompt_en 摘要 |
|-----|--------|--------|---------------|
| `studio` | 棚拍光 | studio lighting | professional studio, softbox, even |
| `natural` | 自然光 | natural daylight | outdoor ambient, soft shadows |
| `dramatic` | 戏剧化光 | dramatic lighting | cinematic, rim light, dark background |
| `softbox` | 柔光箱 | softbox product light | even soft white light |

### 2.3 styles（风格选项）

| key | 中文名 | 英文名 | prompt_en 摘要 |
|-----|--------|--------|---------------|
| `photorealistic` | 实物摄影 | photorealistic | high-resolution photo, real materials |
| `catalog` | 目录商品图 | catalog product photo | clean, isolated on white |
| `technical` | 技术图纸 | technical illustration | isometric, dimensional annotations |
| `3d-render` | 3D 渲染 | 3D render | octane/unreal style, sharp materials |

## 3. Preset 查找优先级

当 Claude 解析 entities 时：

1. 按 `product_category` 选工业品 preset（machinery/equipment/materials）
2. 按 `product_name` 模糊匹配 `products.*` 中的 name_zh/keywords_zh
3. 如未匹配，按 `product_category` 用 preset 默认产品
4. 如 category 是 "other"，用通用 preset（angles/lighting/styles）拼装
5. 拼装顺序：products.keywords_en + 视角 + 光照 + 风格 + scene

## 4. Preset 字段参考

```yaml
# 工业品 preset 必填字段
category: machinery              # 英文 ID
category_zh: 机械类              # 中文分类名

products:                        # 适用产品字典
  casing:                        # 产品 key（英文）
    name_zh: 石油套管            # 中文名（NLU 显示用）
    name_en: OCTG oil casing     # 英文名（prompt 拼装用）
    keywords_zh: [套管, 钻探]    # 中文关键词（NLU 匹配）
    keywords_en: [OCTG, casing]  # 英文关键词（prompt 拼装）
    typical_scene: [油田, 钻井平台]
    default_angle: 45deg
    default_style: catalog

default_lighting: studio         # 通用默认
default_size: 1024x1024
recommended_capability: t2i      # 建议能力
```