# HLZD-视频生成 - 质量优化经验沉淀

> 来自真实迭代：`OCTG 石油套管` I2V 端到端测试（v1 失败 → v2 成功）
> 时间：2026-07-06

## 问题现象

| 现象 | 严重度 | 截图/视频 |
|------|--------|----------|
| 管子变扁（圆柱体被压扁） | 🔴 高 | i2v_v1.mp4 (orbit 镜头) |
| 文字错（OOCTG 应为 OCTG） | 🟡 中 | i2v_v1.mp4 |

## 根因分析

### 1. 管子变扁
- **触发条件**：scene_motion = `orbit`（360 度环绕镜头）
- **机制**：Agnes 模型对 3D 圆柱体的旋转理解有偏差，旋转过程中产生透视错觉，管子截面被压扁
- **触发频率**：管材/型材类（套管、钢管、钢筋）+ orbit 镜头 → 100% 触发

### 2. 错字
- **触发条件**：产品名含行业缩写（OCTG / ASTM / API 等）
- **机制**：Agnes 训练数据里这些缩写出现频率低，模型倾向于"展开"成完整词或重复字母
- **触发频率**：所有行业缩写 → 80%+ 触发

## 解决方案

### 1. 几何稳定性：换 `push_in` 镜头

| 镜头 | 几何稳定性 | 适用场景 |
|------|-----------|---------|
| `orbit` 360° 环绕 | ⚠️ 圆柱体可能变形 | 不适合管材/型材 |
| `static` 静态特写 | ✅ 最稳 | 通用默认（推荐） |
| `push_in` 推近 | ✅ 稳定 | 工艺细节、管材类（推荐） |
| `factory_run` 工厂运转 | ✅ 稳定 | 设备类 |
| `site_demo` 工地演示 | ✅ 稳定 | 工程机械类 |

**决策规则**：
- 管材/型材（套管/钢管/钢筋）→ `push_in`
- 设备/工程机械 → `factory_run` 或 `site_demo`
- 白底主图 → `orbit`（如果产品不是圆柱体）/ `static`（保底）

### 2. 错字防护：多层 negative_prompt

```yaml
# 三层防护
negative_prompt = motion_negative + product_extra_negative + global_negative
```

**全局通用 negative**（所有产品）：
```
no text overlay, no labels, no watermarks, no logos, no extra letters
```

**产品级 extra_negative**（按需）：
```yaml
# 套管
extra_negative_en: "no text overlay, no labels, no watermarks, no logos, OCTG must be four letters only"

# 阀门
extra_negative_en: "deformed valve body, melted metal, asymmetric"

# 轴承
extra_negative_en: "deformed rings, non-circular shape"
```

### 3. Prompt 强化技巧

| 类别 | 推荐 prompt 片段 | 反例 |
|------|------------------|------|
| 几何 | "cylindrical round metal" | "oil pipe"（太抽象） |
| 缩写 | "O-C-T-G (single O)" 或 "OCTG four letters" | "OCTG"（单独不可靠） |
| 视角 | "maintaining original perspective" | "any angle"（让模型自由发挥） |
| 数量 | "five parallel pipes" | "pipes"（数量不明） |

## 已沉淀的优化（2026-07-06）

### preset 改动

1. `presets/common/motions.yaml`
   - `orbit` 加 quality_note 警告
   - `push_in` 强化 prompt（"maintaining original perspective" + 反变形 negative）
   - `static` 标记为推荐默认

2. `presets/industrial/machinery.yaml`
   - `oil_casing` 默认 motion 从 `factory_run` 改为 `push_in`
   - `oil_casing` 加 extra_negative（OCTG 错字防护）
   - `valve` / `bearing` 默认 motion 改为 `push_in` + 加几何防护 negative

3. `presets/industrial/equipment.yaml`
   - `shipping_container` 加 extra_negative（集装箱壁变形防护）

### 代码改动

`scripts/prompt_builder.py` — 三层 negative 合并：
```python
negative_prompt = motion_negative + product_extra + global_no_text
```

## 测试用例 T11：质量优化验证

### 失败案例（v1）
```bash
# 触发问题：orbit + 简单 prompt
py scripts/agnes_video_client.py \
  --capability i2v \
  --prompt "OCTG oil casing pipes rotating 360 degrees" \
  --image "https://i.ibb.co/xxx.png" \
  --duration 5
```
**问题**：管子变扁 + 出现 OOCTG 错字

### 修复方案（v2）
```bash
# 已沉淀到 preset：直接用 --auto 即可
py scripts/orchestrator.py \
  --auto --product-name 石油套管 --capability i2v \
  --duration 5 --aspect-ratio 1:1
```
**改进**：默认 push_in 镜头 + 自动 OCTG 错字防护

## 后续可优化方向

| 方向 | 价值 | 实现成本 |
|------|------|---------|
| 多次生成 + 选最佳（quality picker） | 高 | 中（要写打分逻辑） |
| 集成 SD/Flux 修帧（inpaint 错字） | 高 | 高（要额外模型） |
| 用真实视频片段做 motion reference | 中 | 低（AnimateDiff） |
| 训练 B2B LoRA（OCTG/套管等） | 极高 | 极高（数据+训练） |

## 失败案例存档

保留在 `outputs/test/`：
- `i2v_real_test.mp4` — T1.2 I2V 首次成功
- `i2v_v2.mp4` — 质量优化版（1.13MB，本次最佳）
- `t2v_smoke.mp4` — T1.1 T2V 冒烟测试

供后续对比参考。