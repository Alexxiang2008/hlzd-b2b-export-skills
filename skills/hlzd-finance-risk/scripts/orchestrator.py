#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HLZD 信用证审单 v0.3 — 主入口

三套规则库自动适配：
- Commercial LC  → UCP 600 + ISBP 745
- Standby LC     → ISP98（推荐）或 UCP 600 fallback
- Demand Guarantee → URDG 758

用法：
    python orchestrator.py <lc_file> [--role beneficiary|applicant|guarantor]
    python orchestrator.py --text "..." [--role ...]   # 直接传文本
    python orchestrator.py --type                       # 仅检测 L/C 类型
    python orchestrator.py --doc-type                   # 仅检测文档状态
    python orchestrator.py --help
"""

# === Windows UTF-8 stdio 幂等包装（CLAUDE.md §1 必须保留）===
import io
import sys


def _ensure_utf8_stdio():
    if sys.platform != "win32":
        return
    for _name in ("stdout", "stderr"):
        _stream = getattr(sys, _name, None)
        if _stream is None or not hasattr(_stream, "buffer"):
            continue
        _encoding = getattr(_stream, "encoding", None) or ""
        if "utf-8" in _encoding.lower():
            continue
        _wrapper = io.TextIOWrapper(_stream.buffer, encoding="utf-8", errors="replace")
        setattr(sys, _name, _wrapper)


_ensure_utf8_stdio()
# === end UTF-8 stdio ===

import argparse
import json
import re
from pathlib import Path
from typing import Any


# === 子模块延迟导入（避免 --help 触发加载链 + 重复包装）===
def _load_detector(name: str):
    """延迟导入 detection 子模块（避免 Windows GBK 头冲突）"""
    here = Path(__file__).parent
    sys.path.insert(0, str(here))
    return __import__(name)


def detect_lc_type(text: str) -> str:
    mod = _load_detector("detect_lc_type")
    return mod.detect_lc_type(text)


def detect_doc_type(text: str) -> str:
    mod = _load_detector("detect_doc_type")
    return mod.detect_doc_type(text)


def detect_role(text: str, hlzd_name: str = "HLZD") -> str:
    mod = _load_detector("detect_role")
    return mod.detect_role(text, hlzd_name)


def scan_soft_clauses(text: str, lc_type: str) -> list:
    """软条款扫描：读 catalog 命中关键词"""
    mod = _load_detector("scan_soft_clauses")
    return mod.scan(text, lc_type)


def detect_discrepancies(parsed: dict) -> list:
    """不符点检测：基于 parsed 字段"""
    mod = _load_detector("detect_discrepancies")
    return mod.detect(parsed)


# === 主流程 ===
def run_pipeline(text: str, role: str = "beneficiary", hlzd_name: str = "HLZD") -> dict:
    """14 步工作流（OCR 除外）"""
    result: dict[str, Any] = {
        "skill": "hlzd-lc-review",
        "version": "0.3",
        "input_chars": len(text),
    }

    # [2] 文档类型
    result["doc_type"] = detect_doc_type(text)
    if result["doc_type"] == "TEMPLATE":
        placeholders = re.findall(r"\[insert [a-z\s]+\]", text.lower())
        result["template_placeholders"] = placeholders
        result["status"] = "TEMPLATE_DETECTED"
        return result
    if result["doc_type"] == "DRAFT":
        result["status"] = "DRAFT_DETECTED"
        return result

    # [3] L/C 类型
    result["lc_type"] = detect_lc_type(text)

    # [4] 角色
    if role:
        result["role"] = role
    else:
        result["role"] = detect_role(text, hlzd_name)

    # [7] 软条款扫描
    result["soft_clauses"] = scan_soft_clauses(text, result["lc_type"])

    # [8] 不符点检测（占位 — 真实场景需先 OCR 提取字段）
    result["discrepancies"] = []  # 待 OCR pipeline 接入

    # [11] 综合风险评级
    risk_score = len(result["soft_clauses"]) * 3  # 简化为软条款数 × 3
    if risk_score >= 15:
        result["risk_level"] = "HIGH"
    elif risk_score >= 8:
        result["risk_level"] = "MEDIUM"
    else:
        result["risk_level"] = "LOW"
    result["risk_score"] = risk_score

    # [12] 改单建议（生成 checklist）
    result["amendment_required"] = bool(result["soft_clauses"])

    result["status"] = "OK"
    return result


def read_lc_input(args) -> str:
    """从文件或 --text 读取 L/C 内容"""
    if args.text:
        return args.text
    if args.lc_file:
        p = Path(args.lc_file)
        if not p.exists():
            print(f"[ERROR] 文件不存在: {args.lc_file}", file=sys.stderr)
            sys.exit(2)
        suffix = p.suffix.lower()
        # Claude 已在外部 OCR 过 PDF/图片；这里只读 .txt / .md
        if suffix in {".txt", ".md", ".swift", ".mt700"}:
            return p.read_text(encoding="utf-8", errors="replace")
        print(f"[ERROR] 仅支持 .txt/.md/.swift/.mt700；PDF/图片需先 Claude OCR", file=sys.stderr)
        sys.exit(2)
    print("[ERROR] 必须指定 --lc-file 或 --text", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HLZD 信用证审单 v0.3 — 三套规则库自动适配",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python orchestrator.py --text "DOCUMENTARY CREDIT ..." --role beneficiary
  python orchestrator.py --lc-file ./sample_lc.txt
  python orchestrator.py --text "STANDBY LC ..." --type
        """,
    )
    parser.add_argument("--lc-file", help="L/C 文件路径（.txt/.md/.swift）")
    parser.add_argument("--text", help="直接传 L/C 文本")
    parser.add_argument(
        "--role",
        choices=["beneficiary", "applicant", "guarantor"],
        default="beneficiary",
        help="HLZD 角色（默认 beneficiary）",
    )
    parser.add_argument("--hlzd-name", default="HLZD", help="HLZD 公司名（角色检测用）")
    parser.add_argument("--type", action="store_true", help="仅输出 L/C 类型")
    parser.add_argument("--doc-type", action="store_true", help="仅输出文档状态")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()

    text = read_lc_input(args)

    if args.type:
        result = {"lc_type": detect_lc_type(text)}
    elif args.doc_type:
        result = {"doc_type": detect_doc_type(text)}
    else:
        result = run_pipeline(text, role=args.role, hlzd_name=args.hlzd_name)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()