---
name: hlzd-office-doc
description: "B2B 工业品出口文档生成 v0.1 — 纯 stdlib DOCX 写入 + HLZD 抬头纸 (PI / CI / PL / COA / 合同 / 发票 / 装箱单 / 报价单 / 质检证书 / 抬头模板)。Use when 用户需要生成 B2B 出口单证 (.docx)、填充 HLZD 抬头信息 (公司名 / 地址 / 电话 / 邮箱 / 网址)、把 B2B 调研内容转成客户级 PDF/DOCX 模板。v0.1 仅 stdlib (zipfile + xml)，无 libreoffice / pandoc 依赖；PDF/Excel/PPTX 互转 v0.2 加。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: document-generation
  triggered_by:
    - 出口文档
    - 单证
    - 抬头
    - DOCX
    - PI
    - CI
    - PL
    - COA
    - 报价单
    - 装箱单
    - 合同
    - 发票
    - B2B document
    - letterhead
---

# HLZD Office Doc (v0.1 lightweight)

最小化 .docx 生成器 — **纯 Python stdlib**（zipfile + xml），无需 libreoffice / pandoc / python-docx。

## v0.1 范围（够用）

| 能力 | 状态 |
|---|---|
| 生成 .docx（title + body + letterhead）| ✅ 跑通 |
| HLZD 默认抬头纸 | ✅ 跑通 |
| XML escape（`<script>` `&` `"` 防注入）| ✅ 跑通 |
| 19 个 pytest 单测 | ✅ 全 pass |

## v0.2 范围（不跑通，留作下版）

- 完整 HLZD 抬头纸模板（logo 占位 / 多语言）
- DOCX ↔ PDF 互转（需 libreoffice）
- DOCX ↔ Excel/PPTX 互转（需 libreoffice / pandoc）
- B2B 模板库（合同 / 发票 / COA / 装箱单标准模板）
- Letterhead PDF 渲染

## 用法

```python
from scripts import lib

# 1) 简单 DOCX
lib.generate_minimal_docx(
    "output.docx",
    title="报价单 / Quotation",
    body_lines=[
        "客户: Aramco Trading Co.",
        "产品: API 5CT OCTG Casing",
        "数量: 5000 meters",
        "报价: USD 1450/meter CIF Jeddah",
    ],
    letterhead="深圳海联智达科技有限公司 HLZD",
)

# 2) HLZD 默认抬头
letterhead = lib.standard_letterhead_hlzd()

# 3) 自定义抬头
custom = lib.add_letterhead(
    "ACME Industrial",
    address="...",
    phone="+86 ...",
    email="...",
    website="...",
)

# 4) End-to-end
result = lib.run_pipeline("out.docx", "Title", ["line1", "line2"])
# -> {"output_path": "...", "size_bytes": ..., ...}
```

## CLI（v0.1 stub）

```bash
# 暂无 CLI; v0.2 加 scripts/cli.py
```

## Related Skills

- `hlzd-cold-outreach` (上游) — 邮件 + 报价正文
- `hlzd-quotation-gen` (上游) — 报价数字
- `hlzd-market-report` (姊妹) — HTML 报告 (非 .docx)

## Versioning

| 版本 | 说明 |
|---|---|
| 0.1.0 | 首版：纯 stdlib DOCX 生成 + letterhead + 19 tests |
