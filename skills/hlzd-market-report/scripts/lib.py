"""hlzd-market-report shared library.

提供：
- 7 条 Voice Contract LAWS（来自 b2b-overseas-market-report spec）
- schema 校验（9 节结构）
- HTML 转义
- 错误归类
- 一致性的 ' - ' / em-dash 修正（LAW 2）
"""
from __future__ import annotations

import html
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ================================================================
# 1. 日志
# ================================================================

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-market-report") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# 2. 错误归类
# ================================================================

class MarketReportError(Exception):
    """hlzd-market-report 通用基类。"""

    def __init__(self, message: str, *, source: str = "hlzd-market-report",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


class SchemaError(MarketReportError):
    """输入 schema 缺失必填字段。"""
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


class VoiceContractViolation(MarketReportError):
    """输出违反 Voice Contract LAWS。"""
    def __init__(self, law_id: str, message: str):
        super().__init__(f"[{law_id}] {message}", source="voice_contract", recoverable=False)
        self.law_id = law_id


# ================================================================
# 3. Voice Contract LAWS
# ================================================================
#
# LAW 1 — 第一行 body 必须以 "What I learned:" 起头（或 comparison title for vs query）
# LAW 2 — 用 ' - ' 而不是 — 或 –
# LAW 3 — 引用用 inline markdown link [name](url)
# LAW 4 — 无 trailing Sources: block（footer 是合法的）
# LAW 5 — 所有 claim 必须有 engagement signal 或 2026-dated URL
# LAW 6 — best X 2026 按信号质量排名
# LAW 7 — 不假设用户是某个品牌
#
# 以下函数检查输入数据是否会违反 LAWS；产出再由渲染器自动 normalize。

_EM_DASH = "—"
_EN_DASH = "–"
_HYPHEN_DASH = " - "

LAW_1_BODY_PREFIX = "What I learned:"
LAW_5_CLAIM_FIELDS = ("user_pain", "root_cause", "market_implication", "snippet", "summary")


def normalize_dashes(text: str) -> str:
    """LAW 2 helper — 把 em-dash / en-dash 替换为 ' - '。

    只动空白边的 dash（保留下划线连接符与单独短横线不被误伤）。
    """
    if not text:
        return text
    # em-dash → ' - '
    text = re.sub(r"\s*—\s*", _HYPHEN_DASH, text)
    # en-dash → '-' (也规范成 ' - ')
    text = re.sub(r"\s*–\s*", _HYPHEN_DASH, text)
    return text


def check_law_1(body_text: str) -> Tuple[bool, str]:
    if body_text.lstrip().startswith(LAW_1_BODY_PREFIX):
        return True, ""
    return False, "first non-empty line must start with 'What I learned:'"


def check_law_2(text: str) -> Tuple[bool, str]:
    if _EM_DASH in text or _EN_DASH in text:
        return False, f"em-dash / en-dash detected (use ' - ')"
    return True, ""


def check_law_4(text: str) -> Tuple[bool, str]:
    # 检查末尾 'Sources:' block
    stripped = text.rstrip()
    if re.search(r"\n\s*Sources:\s*\n", stripped + "\n"):
        return False, "trailing 'Sources:' block is forbidden (footer handles citations)"
    if stripped.endswith("Sources:"):
        return False, "trailing 'Sources:' line is forbidden"
    return True, ""


def validate_voice_contract(
    *,
    body_first_line: str = "",
    body_text: str = "",
    candidate_text: str = "",
    has_source_url: bool = True,
    has_brand_assumption: bool = False,
) -> List[VoiceContractViolation]:
    """运行 voice contract 检查 — 返回违例列表（空 list = 通过）。

    所有 checks 是 advisory，不是 hard fail；调用方决定如何处置。
    """
    out: List[VoiceContractViolation] = []
    if body_first_line:
        ok, msg = check_law_1(body_first_line)
        if not ok:
            out.append(VoiceContractViolation("LAW_1", msg))
    if candidate_text:
        ok, msg = check_law_2(candidate_text)
        if not ok:
            out.append(VoiceContractViolation("LAW_2", msg))
    if body_text:
        ok, msg = check_law_4(body_text)
        if not ok:
            out.append(VoiceContractViolation("LAW_4", msg))
    if not has_source_url:
        out.append(VoiceContractViolation("LAW_5", "every claim must cite a URL or engagement signal"))
    if has_brand_assumption:
        out.append(VoiceContractViolation("LAW_7", "do not assume the user IS a particular brand"))
    return out


# ================================================================
# 4. 9 节 schema validation
# ================================================================

REQUIRED_SECTION_KEYS: Dict[str, Iterable[str]] = {
    "cover": ("headline", "tagline", "kpis", "three_step_plan"),
    "toc": (),
    "solution_overview": ("recap", "conclusion_table"),
    "three_signals": ("signals",),
    "platform_deep_dive": ("platforms",),
    "strategic_comparison": ("vendors",),
    "action_plan": ("actions",),
    "methodology": ("five_step", "five_dim", "seven_limitations"),
    "footer_sources": ("sources",),
}

# 这些 section 接受 list 而非 dict（覆盖在 meta + TOC 锚点列表）
LIST_SECTIONS: set = {"toc"}


def validate_schema(report: Dict[str, Any]) -> List[SchemaError]:
    out: List[SchemaError] = []
    for section, required in REQUIRED_SECTION_KEYS.items():
        if section not in report:
            out.append(SchemaError(f"missing section: {section}"))
            continue
        sec = report[section]
        if section in LIST_SECTIONS:
            # list-typed section; just confirm non-empty list when required
            if required and not isinstance(sec, list):
                out.append(SchemaError(f"section {section!r} must be list"))
                continue
        else:
            if not isinstance(sec, dict):
                out.append(SchemaError(f"section {section!r} must be dict"))
                continue
        if isinstance(sec, dict):
            for k in required:
                if k not in sec:
                    out.append(SchemaError(f"section {section!r} missing key {k!r}"))
    return out


# ================================================================
# 5. HTML 转义
# ================================================================

def esc(s: Any) -> str:
    """HTML escape — accepts None / number / string."""
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def url_href(url: str) -> str:
    """URL 简单校验：非空且看起来像 URL。"""
    if not url:
        return "#"
    if not re.match(r"^https?://", url):
        return "#"
    return url


def md_link(name: str, url: str) -> str:
    """Markdown inline link."""
    if not url:
        return name
    if not url.startswith("http"):
        return name
    return f"[{name}]({url})"


# ================================================================
# 6. 时间戳
# ================================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
