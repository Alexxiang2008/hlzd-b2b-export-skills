#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档状态检测 — 模板 / 草稿 / 已签发"""
import re

TEMPLATE_PATTERN = re.compile(r"\[insert [a-z\s]+\]", re.IGNORECASE)
DRAFT_KEYWORDS = ("draft", "watermark", "sample", "specimen", "preview")


def detect_doc_type(text: str) -> str:
    """识别 L/C 文档状态。返回值：TEMPLATE / DRAFT / ISSUED"""
    t = text.lower()

    # 模板: 3+ 个 [Insert XXX] 占位符
    if len(TEMPLATE_PATTERN.findall(t)) >= 3:
        return "TEMPLATE"

    # 草稿: 含 draft / watermark / sample 等关键词
    for kw in DRAFT_KEYWORDS:
        if kw in t:
            return "DRAFT"

    return "ISSUED"


if __name__ == "__main__":
    import sys
    sample = sys.argv[1] if len(sys.argv) > 1 else "ISSUED LC TEXT"
    print(detect_doc_type(sample))