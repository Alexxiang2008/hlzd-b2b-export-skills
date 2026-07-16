---
name: hlzd-knowledge-graph
description: "B2B 实体图谱 —— 从 inquiry / buyer-finder / quotation 输出抽实体 (customer / product / country / cert)，构建内存图，支持 BFS 关系查询 + DOT 导出。Use when 用户说'知识图谱'、'客户关系'、'实体抽取'、'customer graph'、'关联查询'、'knowledge graph'、'B2B graph'、'关联买家'。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: knowledge-graph
  triggered_by:
    - 知识图谱
    - 客户关系
    - 实体抽取
    - customer graph
    - 关联查询
    - knowledge graph
    - B2B graph
    - 关联买家
---

# HLZD Knowledge Graph

B2B 实体抽取 + 轻量内存图 + BFS 查询 + DOT 导出。

## 节点类型

`customer` / `product` / `country` / `certification` / `hs_code` / `supplier`

## 边类型

| 边 | 含义 |
|---|---|
| `interested_in` | customer → product |
| `sourced_from` / `hosted_in` | customer → country |
| `certified_by` | product → certification |
| `classified_under` | product → hs_code |
| `ordered_from` | customer → supplier |
| `complies_with` | product/customer → standard |

## 用法

```python
from scripts import lib

text = "We need OCTG from Saudi Arabia with API 5CT and ISO 9001."
result = lib.run_pipeline(text, customer_name="Aramco",
                           query_product="OCTG",
                           query_country="Saudi Arabia")
# result["extracted_entities"] + result["graph"] + result["queries"]
```

## Output schema

```json
{
  "$schema": "hlzd-knowledge-graph/v1",
  "extracted_entities": {
    "products": ["OCTG", "Steel Pipe"],
    "countries": ["Saudi Arabia"],
    "certifications": ["API 5CT", "ISO 9001"]
  },
  "graph": {
    "nodes": [...],
    "edges": [...],
    "stats": {"node_count": 5, "edge_count": 6, "by_type": {...}}
  },
  "queries": {
    "related_customers_for_product": [...],
    "products_in_country": [...]
  }
}
```

## DOT 导出

```python
import lib
g = lib.build_graph_from_entities(entities)
dot_str = lib.export_dot(g)
# `dot -Tpng > out.png`
```

## Related Skills

- `hlzd-inquiry-qualify` (上游) — inquiry JSON 输入
- `hlzd-buyer-finder` (上游) — buyer JSON 输入
- `hlzd-quotation-gen` (上游) — quote JSON 输入
- `hlzd-pipeline-viz` (下游) — 消费 graph 实体数

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：实体抽取 + 内存图 + BFS + DOT |
