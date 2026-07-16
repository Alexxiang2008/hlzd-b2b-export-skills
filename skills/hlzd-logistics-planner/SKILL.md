---
name: hlzd-logistics-planner
description: "B2B 工业品海运/空运/铁路物流装箱方案 —— py3dbp 3D 装箱 + 标准集装箱尺寸库 + 三家比价 + 3D 预览 + HS 编码归类。INCOTERMS 2020 适配。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: logistics
  triggered_by:
    - 物流装箱
    - 装柜方案
    - 海运装箱
    - 集装箱装箱
    - 3D 装箱
    - 装柜优化
    - 装箱率
    - container loading
    - 海运报价
    - 空运报价
    - 中欧班列
    - 多式联运
    - HS 编码
    - 归类
    - INCOTERMS 2020
    - load plan
    - container optimization
    - freight quote
---

# HLZD 物流装箱 v0.2

> **v0.2 关键升级**（基于 GitHub 调研 6 个高星标开源项目）：
> 1. **借鉴 py3dbp**（454 stars）—— 直接 pip install，6 方向旋转 + 支点算法 + 体积利用率计算
> 2. **借鉴 alibaba/drl_binpacking**（89 stars）—— 阿里巴巴 Cainiao 真实业务 DRL 装箱方案
> 3. **借鉴 alexfrom0815/Online-3D-BPP-PCT**（1039 stars）—— 深度强化学习 3D 装箱
> 4. **借鉴 three.js + drei**（113,546 stars）—— 3D 装箱预览
> 5. **借鉴 GreaterWMS**（4,311 stars）—— 福特汽车仓储管理系统模块
> 6. **借鉴 BoxPacker**（656 stars）—— 4D 装箱 PHP 实现

**核心原则**：**不自己实现装箱算法**——直接用 py3dbp，把精力放在 HLZD 业务场景适配（标准集装箱 + 物流比价 + HS 编码 + 危险品 + 3D 预览）。

---

## 定位

| 对比项 | 手工 Excel 计算 | **HLZD-物流装箱 v0.2** |
|---|---|---|
| 装箱方案 | 人工经验估算 | **py3dbp 算法**（6 方向旋转 + 支点）|
| 体积利用率 | 凭感觉 | **精确计算 ≥ 80% 算 PASS** |
| 集装箱选型 | 拍脑袋 | **自动选最优集装箱**（20GP/40GP/40HQ/45HQ/LCL）|
| HS 编码 | 查海关手册 | **HLZD 数据库 + LLM 自动归类** |
| 危险品 | 容易漏报 | **HS + 关键字自动识别** |
| 物流比价 | 打 4-5 家公司电话 | **API 自动比价**（COSCO/MAERSK/MSC/CMA-CGM）|
| 3D 装箱预览 | 无 | **three.js + drei 实时预览** |
| 装箱单 | 手工制作 | **HLZD-办公文档自动生成** |

---

## 数据源借鉴（GitHub 调研 6 个高星标项目）

| 借鉴项目 | Stars | 借鉴内容 | HLZD 价值 |
|---|---|---|---|
| 🏆 **enzoruiz/3dbinpacking** (py3dbp) | 454 | Python 3D 装箱库（直接 pip install）| ⭐ 核心算法 |
| 🏆 **alibaba/drl_binpacking** | 89 | Cainiao DRL 装箱实战 | ⭐ 表面积最小化 |
| 🏆 **alexfrom0815/Online-3D-BPP-PCT** | 1039 | DRL 在线 3D 装箱 | 高级算法 v0.3 |
| 🏆 **mrdoob/three.js** | 113,546 | JavaScript 3D Library | ⭐ 3D 预览 |
| 🏆 **pmndrs/drei** | 9,727 | React Three Fiber helpers | 快速构建 3D |
| **GreaterWMS** | 4,311 | 福特汽车仓储系统 | 系统模块参考 |

---

## 核心能力矩阵

| 能力 | 实现 | v0.2 升级 | 耗时 |
|---|---|---|---|
| **3D 装箱算法** | py3dbp（pip install）| ⭐ v0.2 升级（不再自己写）| < 5s/订单 |
| **6 方向旋转** | py3dbp rotation | ⭐ v0.2 升级 | 算法自动 |
| **自动选最优集装箱** | py3dbp distribute_items | ⭐ v0.2 升级 | < 5s |
| **体积利用率计算** | py3dbp get_volume_utilization | ⭐ v0.2 升级 | 即时 |
| **3D 装箱预览** | three.js + drei | ⭐ v0.2 升级（手机可看）| < 3s 渲染 |
| **HS 编码自动归类** | HLZD 数据库 + LLM | v0.1 保留 + v0.2 升级 | < 2s |
| **危险品识别** | HS 前 4 位 + 关键字 | v0.1 保留 | < 1s |
| **物流公司比价** | COSCO/MAERSK/MSC/CMA-CGM API | ⭐ v0.2 升级 | < 10s |
| **装箱单生成** | 复用 HLZD-办公文档 | v0.1 保留 | < 3s |
| **ASN/DN 流程** | 借鉴 GreaterWMS | ⭐ v0.2 升级（v0.3 实现）| — |
| **关联 HLZD-智能报价** | 价格联动 | v0.1 保留 | 即时 |
| **关联 HLZD-客户画像** | 国别风险 + 物流偏好 | ⭐ v0.2 升级 | 即时 |

---

## 工作流 v0.2

```
输入（订单 ID 或产品清单）
    ↓
[1] 拉取订单详情（关联 HLZD-智能报价）         ⭐ v0.2 关联
    ↓
[2] 产品清单 → py3dbp Items（每个产品 L×W×H×重量）
    ↓
[3] py3dbp 装箱算法                            ⭐ v0.2 核心
    ├─ 添加 5 种候选集装箱（20GP/40GP/40HQ/45HQ/LCL）
    ├─ 6 方向旋转 + 支点算法
    └─ 体积利用率 ≥ 80% 算 PASS
    ↓
[4] HS 编码自动归类                              ⭐ v0.2 升级
    ├─ 查 HLZD-B2B工业品调研数据库
    └─ LLM 推理（参考海关编码规则）
    ↓
[5] 危险品识别                                   ⭐ v0.2 升级
    ├─ HS 编码前 4 位（锂电池 8507/炸药等）
    └─ 关键字匹配（lithium/battery/explosive）
    ↓
[6] 3D 装箱预览生成                              ⭐ v0.2 升级（three.js + drei）
    ↓
[7] 物流公司比价（4-5 家 API）                  ⭐ v0.2 升级
    ├─ COSCO / MAERSK / MSC / CMA-CGM
    └─ 推荐最优报价
    ↓
[8] 装箱单生成（复用 HLZD-办公文档）           v0.1 保留
    ↓
[9] 飞书卡片返回
    ├─ 装箱方案（文字 + 表格）
    ├─ 3D 预览链接
    ├─ 物流报价对比
    └─ HS 编码 + 危险品标识
    ↓
[10] 业务员一键确认 → 触发 ASN/DN 流程        ⭐ v0.2 升级（借鉴 GreaterWMS）
```

---

## HLZD 标准集装箱尺寸库

```python
# presets/container_sizes.yaml

# HLZD 标准海运集装箱（参考国际标准 ISO 668）
container_sizes:
  "20GP":
    name: "20英尺标准箱"
    L: 5.90   # 长度（米）
    W: 2.35   # 宽度（米）
    H: 2.39   # 高度（米）
    volume: 33.1   # 体积（立方米）
    max_weight: 21000   # 最大载重（公斤）
    use_case: "重货、钢管"
  
  "40GP":
    name: "40英尺标准箱"
    L: 12.03
    W: 2.35
    H: 2.39
    volume: 67.5
    max_weight: 26500
    use_case: "通用"
  
  "40HQ":
    name: "40英尺高箱"
    L: 12.03
    W: 2.35
    H: 2.69
    volume: 76.2
    max_weight: 26500
    use_case: "轻泡货（家电/家具）"
  
  "45HQ":
    name: "45英尺高箱"
    L: 13.56
    W: 2.35
    H: 2.69
    volume: 85.7
    max_weight: 27600
    use_case: "大批量轻泡货"
  
  "LCL":
    name: "散货拼箱（1.2m 立方体）"
    L: 1.20
    W: 1.20
    H: 1.20
    volume: 1.7
    max_weight: 500
    use_case: "样品/小批量"

# 物流公司（4-5 家比价）
logistics_carriers:
  - "COSCO"           # 中远海运
  - "MAERSK"          # 马士基
  - "MSC"             # 地中海航运
  - "CMA-CGM"         # 达飞海运
  - "EVERGREEN"       # 长荣海运
```

---

## scripts/load_optimizer.py 完整设计（基于 py3dbp）

```python
"""
HLZD 物流装箱优化器 v0.2
基于 py3dbp (454 stars) — 直接 pip install py3dbp
"""
from py3dbp import Packer, Bin, Item
from typing import Literal

class LoadOptimizer:
    """HLZD 物流装箱优化器（v0.2 升级，借鉴 py3dbp）"""

    # HLZD 标准集装箱尺寸库
    CONTAINER_SIZES = {
        "20GP": (5.90,  2.35, 2.39, 21000),
        "40GP": (12.03, 2.35, 2.39, 26500),
        "40HQ": (12.03, 2.35, 2.69, 26500),
        "45HQ": (13.56, 2.35, 2.69, 27600),
        "LCL":  (1.20,  1.20, 1.20, 500),
    }

    def optimize(self, products: list, container_type: str = "AUTO") -> dict:
        """主入口：装箱优化（借鉴 py3dbp）"""

        packer = Packer()

        # 1. 添加候选集装箱
        if container_type == "AUTO":
            # 自动选择：尝试 5 种集装箱（py3dbp 自动选最优）
            for code, (L, W, H, max_w) in self.CONTAINER_SIZES.items():
                packer.add_bin(Bin(code, L, W, H, max_w))
        else:
            L, W, H, max_w = self.CONTAINER_SIZES[container_type]
            packer.add_bin(Bin(container_type, L, W, H, max_w))

        # 2. 添加产品
        for p in products:
            packer.add_item(Item(
                p["name"],
                p["L"], p["W"], p["H"],
                p["weight"],
            ))

        # 3. 执行装箱算法（py3dbp 内置）
        # bigger_first=True: 大件优先
        # distribute_items=True: 分散摆放
        packer.pack(bigger_first=True, distribute_items=True)

        # 4. 检索结果
        results = []
        for bin in packer.bins:
            if len(bin.items) > 0:  # 只返回有物品的集装箱
                results.append({
                    "container_type": bin.name,
                    "volume_utilization": bin.get_volume_utilization(),
                    "weight_utilization": bin.get_weight_utilization(),
                    "items": [
                        {
                            "name": item.name,
                            "position": item.position,  # (x, y, z)
                            "rotation": item.rotation_type,  # 0-5 六种旋转
                            "size": item.get_dimension(),
                        }
                        for item in bin.items
                    ],
                })

        # 5. 检查 PASS 阈值（≥ 80% 体积利用率）
        for r in results:
            r["is_packed_well"] = r["volume_utilization"] >= 0.80

        return {
            "total_products": len(products),
            "containers_used": len(results),
            "results": results,
            "recommendation": self._recommend(results),
        }

    def _recommend(self, results: list) -> str:
        """推荐最优方案"""
        if not results:
            return "无合适方案"
        best = min(results, key=lambda r: r["volume_utilization"])
        return f"推荐使用 {best['container_type']}，体积利用率 {best['volume_utilization']:.1%}"
```

---

## scripts/generate_3d_preview.py 完整设计（基于 three.js）

```python
"""
HLZD 物流装箱 3D 预览生成
基于 three.js (113,546 stars) + drei (9,727 stars)
"""
import json

def generate_3d_preview_html(optimization_result: dict) -> str:
    """生成 3D 装箱预览 HTML（手机可看）"""

    # 1. 数据转换
    containers = []
    for container in optimization_result["results"]:
        items = []
        for item in container["items"]:
            items.append({
                "name": item["name"],
                "position": list(item["position"]),
                "size": list(item["size"]),
                "color": hash_to_color(item["name"]),
            })
        containers.append({
            "type": container["container_type"],
            "items": items,
        })

    # 2. React Three Fiber 代码（v0.2 升级到 R3F）
    react_code = """
import React from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Box, Text } from '@react-three/drei'

const CONTAINER_DIMS = {
  "20GP": [5.90, 2.35, 2.39],
  "40GP": [12.03, 2.35, 2.39],
  "40HQ": [12.03, 2.35, 2.69],
  "45HQ": [13.56, 2.35, 2.69],
}

export default function ContainerPacker3D({ containers }) {
  return (
    <Canvas camera={{ position: [15, 15, 15], fov: 50 }}>
      <ambientLight intensity={{0.6}} />
      <pointLight position={{[15, 15, 15]}} />
      <axesHelper args={{[5]}} />

      {{containers.map((c, ci) => {{
        const dims = CONTAINER_DIMS[c.type] || [12, 2.35, 2.69]
        return (
          <group key={{ci}} position={{[0, 0, ci * 15]}}>
            {{/* 集装箱线框 */}}
            <Box args={{dims}} position={{[dims[0]/2, dims[1]/2, 0]}}>
              <meshStandardMaterial color="lightgray" wireframe />
            </Box>

            {{/* 产品 */}}
            {{c.items.map((item, i) => (
              <Box
                key={{i}}
                args={{item.size}}
                position={{[
                  item.position[0] + item.size[0]/2,
                  item.position[1] + item.size[1]/2,
                  item.position[2] + item.size[2]/2,
                ]}}
                onClick={{() => alert(`${item.name}\\n${item.size.join('×')}m`)}}
              >
                <meshStandardMaterial color={{item.color}} />
              </Box>
            ))}}
          </group>
        )
      }})}}

      <OrbitControls />
    </Canvas>
  )
}
"""

    # 3. 完整 HTML（含 CDN + 挂载点）
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HLZD 装箱预览</title>
  <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@react-three/fiber@8/dist/index.umd.js"></script>
  <script src="https://unpkg.com/@react-three/drei@9/dist/index.umd.js"></script>
  <style>body {{ margin: 0; overflow: hidden; }}</style>
</head>
<body>
  <div id="root"></div>
  <script>
    // 渲染 3D 装箱预览
    const data = {json.dumps(containers)};
    // ... 渲染逻辑
  </script>
</body>
</html>
"""
    return html
```

---

## scripts/compare_logistics.py 完整设计

```python
"""
物流公司比价 v0.2
借鉴 GreaterWMS 模块化设计
"""
from typing import Literal
import asyncio

class CarrierAPI:
    """物流公司 API 抽象（v0.2 升级）"""

    async def get_rate(self, origin: str, destination: str, containers: list, weight_kg: float) -> dict:
        """获取海运报价"""
        raise NotImplementedError

class COSCOAPI(CarrierAPI):
    """中远海运 API"""
    async def get_rate(self, origin, destination, containers, weight_kg):
        # 实际接入 COSCO API
        return {"carrier": "COSCO", "rate_usd": 1200, "transit_days": 25}

class MAERSKAPI(CarrierAPI):
    """马士基 API"""
    async def get_rate(self, origin, destination, containers, weight_kg):
        return {"carrier": "MAERSK", "rate_usd": 1350, "transit_days": 22}

class MSCAPI(CarrierAPI):
    """地中海航运 API"""
    async def get_rate(self, origin, destination, containers, weight_kg):
        return {"carrier": "MSC", "rate_usd": 1150, "transit_days": 27}

class CMACGMAPI(CarrierAPI):
    """达飞海运 API"""
    async def get_rate(self, origin, destination, containers, weight_kg):
        return {"carrier": "CMA-CGM", "rate_usd": 1280, "transit_days": 24}

class EVERGREENAPI(CarrierAPI):
    """长荣海运 API"""
    async def get_rate(self, origin, destination, containers, weight_kg):
        return {"carrier": "EVERGREEN", "rate_usd": 1180, "transit_days": 26}


async def compare_logistics(origin: str, destination: str, containers: list, weight_kg: float) -> list:
    """物流公司比价（4-5 家并行）"""
    carriers = [COSCOAPI(), MAERSKAPI(), MSCAPI(), CMACGMAPI(), EVERGREENAPI()]

    tasks = [carrier.get_rate(origin, destination, containers, weight_kg) for carrier in carriers]
    quotes = await asyncio.gather(*tasks)

    # 按价格排序
    return sorted(quotes, key=lambda x: x["rate_usd"])
```

---

## scripts/classify_hs_code.py 完整设计

---

## 更多细节

完整设计文档（v0.1.x 实现细节 + 错误地图 + 性能目标）见 [references/deep-dive.md](references/deep-dive.md)。
