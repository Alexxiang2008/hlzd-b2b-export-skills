"""hlzd-buyer-finder shared library.

提供 4 个脚本 / 3 个 source adapter 共享的基础设施：
- 日志
- 错误归类（含 Volza blocked detection 的确定性算法）
- 防封计数器（rate limiter）
- 公司名 dedup
- 字段 schema 校验

设计原则：所有 deterministic 逻辑必须不依赖网络就能跑，便于 100% 单测覆盖。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ================================================================
# 1. 日志
# ================================================================

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-buyer-finder") -> logging.Logger:
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

class BuyerFinderError(Exception):
    """hlzd-buyer-finder 通用基类。"""

    def __init__(self, message: str, *, source: str = "hlzd-buyer-finder",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_class": self.__class__.__name__,
            "message": str(self),
            "source": self.source,
            "recoverable": self.recoverable,
        }


class SourceBlockedError(BuyerFinderError):
    """Volza / ImportGenius 等数据源被反爬（付费墙 / captcha）。"""
    def __init__(self, message: str, source_name: str):
        super().__init__(message, source=source_name, recoverable=True)


class RateLimitedError(BuyerFinderError):
    """429 / 调用次数到上限。"""
    def __init__(self, message: str, source_name: str, retry_after: int = 60):
        super().__init__(message, source=source_name, recoverable=True)
        self.retry_after = retry_after


class InvalidParameterError(BuyerFinderError):
    """调用参数错误（不应 retry）。"""
    def __init__(self, message: str, source_name: str = "hlzd-buyer-finder"):
        super().__init__(message, source=source_name, recoverable=False)


# ================================================================
# 3. Rate limiter + 日配额
# ================================================================

class RateLimiter:
    """进程内的简单 rate limiter，支持 (a) 间隔 + (b) 日配额。

    state 持久化在 ~/.cache/hlzd-buyer-finder/rate_state.json，
    让多次 CLI 调用共享配额。
    """

    DEFAULT_STATE_PATH = Path.home() / ".cache" / "hlzd-buyer-finder" / "rate_state.json"

    def __init__(self, name: str, min_interval_sec: float = 5.0,
                 daily_quota: int = 10, state_path: Optional[Path] = None):
        self.name = name
        self.min_interval = min_interval_sec
        self.daily_quota = daily_quota
        self.state_path = state_path or self.DEFAULT_STATE_PATH
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                return data.get(self.name, {"date": today, "count": 0, "last_ts": 0.0})
            except Exception:
                pass
        return {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "count": 0, "last_ts": 0.0}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        all_data: Dict[str, Any] = {}
        if self.state_path.exists():
            try:
                all_data = json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                all_data = {}
        all_data[self.name] = self._state
        self.state_path.write_text(
            json.dumps(all_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _rollover_if_new_day(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._state.get("date") != today:
            self._state = {"date": today, "count": 0, "last_ts": 0.0}

    def can_call(self) -> Tuple[bool, str]:
        """Return (allowed, reason)。"""
        self._rollover_if_new_day()
        if self._state["count"] >= self.daily_quota:
            return False, (f"daily quota exhausted ({self._state['count']}/"
                           f"{self.daily_quota} for {self.name})")
        elapsed = time.time() - float(self._state.get("last_ts", 0))
        if elapsed < self.min_interval:
            return False, (f"interval too short ({elapsed:.1f}s < {self.min_interval}s)")
        return True, "ok"

    def record_call(self) -> None:
        self._state["count"] = int(self._state.get("count", 0)) + 1
        self._state["last_ts"] = time.time()
        self._save_state()

    def reset(self) -> None:
        """强制重置（用于测试）。"""
        self._state = {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                       "count": 0, "last_ts": 0.0}
        self._save_state()

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "today": self._state["date"],
            "used": int(self._state.get("count", 0)),
            "quota": self.daily_quota,
            "min_interval_sec": self.min_interval,
        }


# ================================================================
# 4. Dedup + 评分
# ================================================================

# B2B 平台 supplier 噪音 URL pattern（来自 customs-data-find SOP）
PLATFORM_NOISE_URL_PATTERNS: List[str] = [
    "alibaba.com", "made-in-china.com", "globalsources.com",
    "indiamart.com", "ec21.com", "tradekey.com", "ecplaza.net",
    "homedepot.com", "lowes.com", "amazon.com", "ebay.com",
    "pinterest.com",  # 装饰图
    "wikipedia.org",  # 一般知识
]


def looks_like_supplier_page(url: str) -> bool:
    url_l = url.lower()
    return any(p in url_l for p in PLATFORM_NOISE_URL_PATTERNS)


def _parse_money(value: Any) -> float:
    """Safely convert a money string / number to float for dedup sorting.

    Accepts:
      - 1234.5 (number or numeric string)
      - "$1,234" / "€500" / "100 USD" (money string with currency / commas)
      - "" / None (returns 0)
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return 0.0
    # Strip $, €, £, ¥, commas, spaces
    s = re.sub(r"[$€£¥,\s]", "", s)
    # Strip trailing currency words
    s = re.sub(r"(USD|EUR|GBP|CNY|RMB|JPY|usd|eur)$", "", s.strip(), flags=re.IGNORECASE)
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def normalize_company_name(name: str) -> str:
    """用于 dedup：去除空格 / 大小写 / 常见公司后缀。

    >>> normalize_company_name("  Acme Co., Ltd.  ")
    'acme'
    """
    s = name.strip().lower()
    s = re.sub(r"[.,\s]+", " ", s).strip()
    for suffix in ("co ltd", "co ltd.", "co., ltd.", "co.,ltd.", "co. ltd.",
                    "limited", "ltd.", "ltd", "llc", "inc.", "inc",
                    "corp.", "corp", "corporation", "gmbh",
                    "s a", "s.a.", "s.a", "s l", "s.l.", "s.l",
                    "company", "co.", "co"):
        s = re.sub(rf"\s+{re.escape(suffix)}\s*$", "", s)
    s = s.strip()
    # 截断 hash 防过长
    return s[:80]


def dedup_importers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按公司名归一化 + URL 去重，保留货运量最大的。

    输入每条需要至少 'importer_name' 或 'url' 字段。
    value 字段支持数字或字符串（"$1,234" / "100 USD" 等）。
    """
    by_name: Dict[str, Dict[str, Any]] = {}
    by_url: Dict[str, Dict[str, Any]] = {}

    for rec in records:
        name = rec.get("importer_name") or rec.get("company_name") or ""
        url = rec.get("url") or ""
        score = _parse_money(rec.get("value_usd") or rec.get("value"))
        key_name = normalize_company_name(name) if name else ""
        key_url = url.lower().strip() if url else ""

        if key_name and key_name in by_name:
            existing = by_name[key_name]
            if score > _parse_money(existing.get("value_usd") or existing.get("value")):
                by_name[key_name].update(rec)
        elif key_name:
            by_name[key_name] = rec
        elif key_url and key_url in by_url:
            existing = by_url[key_url]
            if score > _parse_money(existing.get("value_usd") or existing.get("value")):
                by_url[key_url].update(rec)
        elif key_url:
            by_url[key_url] = rec
        else:
            # 兜底：每条都不同（无 key）
            by_url[f"__anon_{len(by_url)}"] = rec

    out = list(by_name.values()) + list(by_url.values())
    # 按 USD 价值降序（接受 string value）
    out.sort(key=lambda r: -_parse_money(r.get("value_usd") or r.get("value")))
    return out


# ================================================================
# 5. Volza blocked detection (deterministic, no network required)
# ================================================================

VOLZA_BLOCKED_BODY_LEN_THRESHOLD = 11055   # 屏蔽页 ≈ 11055 bytes
VOLZA_SUCCESS_BODY_LEN_MIN = 15000         # 搜索成功 > 15000


def classify_volza_response(body: str, body_len: Optional[int] = None) -> str:
    """根据返回 body 长度判断 Volza 响应状态。

    Returns: 'blocked' | 'success' | 'loading' | 'unknown'
    """
    if body_len is None:
        body_len = len(body.encode("utf-8") if isinstance(body, str) else body)
    diff = abs(body_len - VOLZA_BLOCKED_BODY_LEN_THRESHOLD)
    if diff < 200:
        return "blocked"
    if body_len >= VOLZA_SUCCESS_BODY_LEN_MIN:
        return "success"
    if VOLZA_BLOCKED_BODY_LEN_THRESHOLD < body_len < VOLZA_SUCCESS_BODY_LEN_MIN:
        return "loading"
    return "unknown"


# ================================================================
# 6. Output schema 校验
# ================================================================

REQUIRED_FIELDS_BY_KIND: Dict[str, Iterable[str]] = {
    "competitor_record": ("company_name", "source"),
    "importer_record": ("importer_name", "country", "url"),
    "pipeline_report": ("product", "country", "method", "competitors", "importers", "warnings"),
}


def assert_shape(payload: Dict[str, Any], kind: str) -> None:
    expected = REQUIRED_FIELDS_BY_KIND.get(kind, ())
    missing = [k for k in expected if k not in payload]
    if missing:
        raise BuyerFinderError(
            f"{kind} payload missing required keys: {missing}",
            source=f"assert_shape",
            recoverable=False,
        )


# ================================================================
# 7. Alibaba 公司名抽取（确定性 regex）
# ================================================================

# 判定"看起来像中国公司名"的特征关键词
CN_COMPANY_INDICATORS = [
    "co.", "ltd", "limited", "inc.", "corp", "factory",
    "industry", "industries", "group", "manufacturing", "technology",
    "industrial", "trading",
]


def extract_company_candidates_from_text(text: str) -> List[str]:
    """从原始文本/HTML 中挑出看起来像中国供应商公司名的候选。

    用于阿里搜索结果页：返回 list[str] (去重保留 80 字符内)
    """
    seen: Dict[str, None] = {}
    out: List[str] = []
    for line in text.splitlines():
        clean = line.strip()
        if len(clean) < 4 or len(clean) > 120:
            continue
        low = clean.lower()
        if not any(ind in low for ind in CN_COMPANY_INDICATORS):
            continue
        # 排除中文夹杂或纯中文
        if re.search(r"[一-鿿]", clean):
            continue
        if clean in seen:
            continue
        seen[clean] = None
        out.append(clean[:80])
    return out


# ================================================================
# 8. Hash / ID
# ================================================================

def stable_id(payload: Any, prefix: str = "id") -> str:
    """生成 sha256-based stable id，用于去重 / 数据库主键。"""
    s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return f"{prefix}:{hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]}"
