# hlzd-logistics-planner — Deep Dive

> 本文件收纳 SKILL.md 因 500 行约束移出的细节章节，仅供 deep-load 参考。


```python
"""
HS 编码自动归类 v0.2
基于 HLZD-B2B工业品调研数据 + LLM
"""
from typing import Optional

# HLZD 内部 HS 编码库（基于 HLZD-B2B工业品调研）
HLZD_HS_DATABASE = {
    "石油套管": "7304.29",
    "阀门": "8481.30",
    "蝶阀": "8481.30",
    "钢管": "7306.30",
    "锂电池": "8507.60",  # 危险品
    "铝型材": "7604.29",
    # ... 5000+ HLZD 产品 HS 编码
}

def classify_hs_code(product_name: str, product_category: str) -> dict:
    """HS 编码自动归类"""

    # 1. 先查 HLZD 内部数据库
    if product_name in HLZD_HS_DATABASE:
        return {
            "hs_code": HLZD_HS_DATABASE[product_name],
            "source": "HLZD_INTERNAL_DB",
            "confidence": 0.95,
        }

    # 2. LLM 推理（参考海关编码规则）
    prompt = f"""根据产品描述推断 HS 编码（6 位）:
    产品: {product_name}
    类别: {product_category}

    HS 编码规则:
    - 第 1-2 位: 章节（如 73=钢铁，84=机器）
    - 第 3-4 位: 品目
    - 第 5-6 位: 子目

    输出格式: XXXX.XX
    """
    hs_code = llm_complete(prompt)

    return {
        "hs_code": hs_code,
        "source": "LLM_INFERENCE",
        "confidence": 0.70,
    }


def detect_hazmat(hs_code: str, product_name: str) -> dict:
    """危险品识别（v0.2 升级）"""

    # 危险品 HS 编码（联合国危险品分类）
    HAZMAT_HS_CODES = {
        "8507": "锂电池（UN3480/UN3481）",
        "3606": "烟花爆炸品",
        "2710": "汽油/柴油",
        "2918": "易燃液体",
        "2926": "易燃固体",
        "3077": "危险环境污染物",
    }

    # 关键字识别
    HAZMAT_KEYWORDS = ["lithium", "battery", "explosive", "flammable", "chemical",
                       "锂电池", "电池", "易燃", "爆炸", "化学品"]

    # 1. HS 编码前 4 位检查
    hs_4digit = hs_code[:4] if hs_code else ""
    if hs_4digit in HAZMAT_HS_CODES:
        return {"is_hazmat": True, "category": HAZMAT_HS_CODES[hs_4digit], "source": "HS_CODE"}

    # 2. 关键字检查
    product_lower = product_name.lower()
    for kw in HAZMAT_KEYWORDS:
        if kw in product_lower:
            return {"is_hazmat": True, "category": f"关键字匹配: {kw}", "source": "KEYWORD"}

    return {"is_hazmat": False, "category": None, "source": "NONE"}
```

---

## scripts/ 设计 v0.2

```
scripts/
├── load_optimizer.py              # ⭐ v0.2: 基于 py3dbp 装箱优化
├── generate_3d_preview.py          # ⭐ v0.2: three.js 3D 预览生成
├── compare_logistics.py            # ⭐ v0.2: 4-5 家物流公司比价
├── classify_hs_code.py             # ⭐ v0.2: HS 编码自动归类 + 危险品识别
├── gen_packing_list.py             # v0.1 保留: 装箱单生成（复用 HLZD-办公文档）
├── asn_dn_workflow.py              # ⭐ v0.2 升级: ASN/DN 流程（借鉴 GreaterWMS）
├── container_sizes.py              # ⭐ v0.2: HLZD 标准集装箱尺寸库
├── carrier_clients.py              # ⭐ v0.2: 4-5 家物流公司 API 客户端
├── stats.py                        # 装箱统计
└── orchestrator.py                 # 主调度
```

---

## references/ 设计 v0.2

```
references/
├── py3dbp_api_reference.md          # ⭐ v0.2: py3dbp API 完整参考
├── container_iso_standards.md      # ⭐ v0.2: ISO 668 集装箱标准
├── hs_code_chapters.md             # ⭐ v0.2: HS 编码章节速查
├── hazmat_classification.md        # ⭐ v0.2: 联合国危险品分类
├── three_js_r3f_quickstart.md      # ⭐ v0.2: three.js + React Three Fiber
├── carrier_api_comparison.md       # ⭐ v0.2: 4-5 家物流公司 API 对比
├── greaterwms_architecture.md      # ⭐ v0.2: 福特仓储系统数据模型参考
├── alibaba_drl_paper.md            # ⭐ v0.2: 阿里巴巴 DRL 装箱论文
├── incoterms_2020.md               # v0.1 保留
└── examples/
    ├── case_40hq_packing.md         # 40HQ 高箱装箱样例
    ├── case_lcl_consolidation.md    # LCL 散货拼箱样例
    ├── case_hazmat_lithium.md       # 锂电池危险品样例
    ├── case_3d_preview.md            # 3D 预览样例
    └── case_logistics_comparison.md # 物流比价样例
```

---

## presets/ 设计 v0.2

```yaml
# presets/container_sizes.yaml
# （见上面完整定义）

# presets/optimizer_config.yaml
optimizer_config:
  default_strategy: "bigger_first"  # 大件优先
  distribute_items: true
  min_volume_utilization: 0.80  # ≥ 80% 算 PASS
  max_container_count: 3  # 最多用 3 个集装箱

# presets/carrier_apis.yaml
carrier_apis:
  COSCO:
    api_url: "https://api.coscoshipping.com"
    auth: "API_KEY"
  MAERSK:
    api_url: "https://api.maersk.com"
    auth: "OAUTH2"
  MSC:
    api_url: "https://api.msc.com"
    auth: "API_KEY"
  CMA-CGM:
    api_url: "https://api.cma-cgm.com"
    auth: "API_KEY"
  EVERGREEN:
    api_url: "https://api.evergreen-line.com"
    auth: "API_KEY"

# presets/hazmat_rules.yaml
hazmat_rules:
  lithium_battery:
    hs_codes: ["8507.60", "8507.80"]
    keywords: ["lithium", "battery", "锂电池", "电池"]
    special_handling: "UN3480/UN3481 申报"
  flammable_liquid:
    hs_codes: ["2710.00", "2918.99"]
    keywords: ["gasoline", "diesel", "易燃"]
    special_handling: "MSDS + 危险品包装"
  explosive:
    hs_codes: ["3606.00"]
    keywords: ["firework", "explosive", "烟花", "爆炸"]
    special_handling: "禁止航空/海运"
```

---

## 错误地图

| 异常 | 触发 | 处理 | 用户看到 |
|---|---|---|---|
| `Py3dbpImportError` | py3dbp 未安装 | 自动 pip install py3dbp | "正在安装 py3dbp..." |
| `ContainerOverflowError` | 产品超过最大集装箱 | 建议拆单 | "⚠️ 订单过大，建议拆单" |
| `WeightOverloadError` | 超重 | 提示分批 | "⚠️ 超重，请分批" |
| `HSCodesError` | HS 编码无法推断 | 提示人工 | "请人工确认 HS 编码" |
| `CarrierAPIError` | 物流 API 失败 | 跳过该家 + 重试 | "COSCO 报价失败，已跳过" |
| `HazmatWarningError` | 检测到危险品 | 强制人工确认 | "⚠️ 锂电池，需危险品申报" |
| `ThreeJsError` | 3D 预览生成失败 | 退回 2D 平面图 | "3D 预览失败，已生成 2D 图" |

---

## 自动串联规则

```markdown
## 自动串联

### 上游
- HLZD-智能报价: 客户确认报价 → 自动触发装箱优化
- HLZD-客户档案: 国别风险 → 推荐物流公司（制裁国家跳过某些）
- HLZD-询盘响应: 物流类询盘 → 自动触发装箱演示

### 下游
- HLZD-办公文档: 装箱单生成
- HLZD-email-group: 装箱方案邮件发送给客户
- 飞书卡片: 业务员确认 → 触发 ASN/DN（v0.3）

### 被动串联
- 装期前 7 天 → 提醒业务员
- 物流报价更新 → 自动重新比价
- HS 编码变更 → 重新归类
```

---

## 验证清单

- [ ] py3dbp 集成（pip install py3dbp）
- [ ] 5 种集装箱选型（20GP/40GP/40HQ/45HQ/LCL）
- [ ] 6 方向旋转测试
- [ ] 体积利用率 ≥ 80% PASS 检查
- [ ] 3D 装箱预览生成（手机可看）
- [ ] HS 编码自动归类（HLZD 数据库 + LLM）
- [ ] 危险品识别（HS + 关键字）
- [ ] 4-5 家物流公司比价
- [ ] 装箱单生成（HLZD-办公文档）
- [ ] ASN/DN 流程（v0.3 实现）

---

## 性能目标

| 路径 | v0.1 | v0.2 |
|---|---|---|
| 装箱优化（10 个产品）| < 5s | **< 2s**（py3dbp）|
| 3D 预览生成 | 不支持 | **< 3s** |
| HS 编码归类 | < 2s | < 1s（HLZD DB 命中）|
| 物流比价（4-5 家）| 不支持 | **< 10s**（并行）|
| 装箱单生成 | < 3s | < 3s（复用 HLZD-办公文档）|

---

## 安全考虑

1. **物流 API 凭证加密**——Panmira secrets 存储
2. **危险品数据隔离**——锂电池/爆炸品单独加密
3. **装箱方案审计**——所有装箱方案保留 5 年
4. **国别合规**——制裁国家自动跳过对应物流公司
5. **客户数据脱敏**——装箱方案共享时脱敏客户信息

---

## 已知限制（v0.2 接受）

1. **DRL 算法未集成**（alibaba/drl_binpacking）—— v0.3
2. **ASN/DN 流程仅占位**（借鉴 GreaterWMS）—— v0.3 实现
3. **物流 API 模拟**——v0.2 用 mock，v0.3 接真实 API
4. **3D 预览无交互**——v0.3 加拖拽旋转/剖面查看
5. **多式联运**（海运+陆运）—— v0.3

---

## 后续路线

| 版本 | 新增 |
|---|---|
| v0.2 | ✅ py3dbp + three.js + 物流比价 + HS 编码 + 危险品 |
| **v0.3** | DRL 装箱（alibaba/drl_binpacking）|
| **v0.3** | ASN/DN 流程实现（借鉴 GreaterWMS）|
| **v0.3** | 多式联运优化（海运+中欧班列+陆运）|
| v0.4 | 实时物流追踪 |
| v0.4 | 集装箱预订集成 |

---

## 文件位置

```
目标位置: ~/.claude/skills/hlzd-shipment/
SKILL.md: ~/.claude/skills/hlzd-shipment/SKILL.md
presets/: ~/.claude/skills/hlzd-shipment/presets/
references/: ~/.claude/skills/hlzd-shipment/references/
scripts/: ~/.claude/skills/hlzd-shipment/scripts/
```

---

**END of HLZD-物流装箱 v0.2 SKILL.md**

**关键借鉴 6 个开源项目**：
- 🏆 **enzoruiz/3dbinpacking**（454 stars）—— **py3dbp 直接 pip install**（不再自己写算法）
- 🏆 **alibaba/drl_binpacking**（89 stars）—— Cainiao 真实业务 DRL 装箱
- 🏆 **alexfrom0815/Online-3D-BPP-PCT**（1039 stars）—— DRL 在线 3D 装箱
- 🏆 **mrdoob/three.js**（113,546 stars）—— JavaScript 3D
- 🏆 **pmndrs/drei**（9,727 stars）—— React Three Fiber helpers
- **GreaterWMS**（4,311 stars）—— 福特汽车仓储管理系统