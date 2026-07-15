"""hlzd-b2b-research shared library.

提供 4 个脚本共享的基础设施：
- 日志统一封装（替代脚本里的 print）
- 错误归类与重试装饰器
- 输出 schema 校验（用于 orchestrator）
- 简易缓存（避免重复 API 调用）

不依赖任何外部库，仅用标准库。
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, TypeVar

# ================================================================
# 1. 日志
# ================================================================

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-b2b-research") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# 2. 错误归类
# ================================================================

class ResearchError(Exception):
    """hlzd-b2b-research 通用错误基类。"""

    def __init__(self, message: str, *, source: str = "hlzd-b2b-research"):
        super().__init__(message)
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {"error_class": self.__class__.__name__, "message": str(self), "source": self.source}


class HSCodeError(ResearchError):
    """HS 编码查询失败（hsbianma.com timeout / 不可达）。"""

    def __init__(self, message: str):
        super().__init__(message, source="hs_lookup")


class TradeDataError(ResearchError):
    """UN Comtrade 查询失败（无数据 / 限流）。"""

    def __init__(self, message: str):
        super().__init__(message, source="trade_data")


class TrendsError(ResearchError):
    """Google Trends 查询失败（429 / timeout）。"""

    def __init__(self, message: str):
        super().__init__(message, source="keyword_trends")


class BuyerSearchError(ResearchError):
    """DDGS 买家搜索失败。"""

    def __init__(self, message: str):
        super().__init__(message, source="buyer_search")


# ================================================================
# 3. 重试装饰器（指数退避）
# ================================================================

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    retry_on: Tuple[type, ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """指数退避重试装饰器：attempt N 时等待 base_delay * 2^(N-1)。

    >>> @retry(max_attempts=3, retry_on=(TradeDataError,))
    >>> def fetch(): ...
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger = get_logger()
            last_exc: Optional[BaseException] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except retry_on as exc:  # type: ignore[misc]
                    last_exc = exc
                    if attempt >= max_attempts:
                        logger.error("[%s] 重试 %d 次仍失败: %s", fn.__name__, attempt, exc)
                        raise
                    wait = base_delay * (2 ** (attempt - 1))
                    logger.warning("[%s] 第 %d 次失败，%ss 后重试: %s", fn.__name__, attempt, wait, exc)
                    time.sleep(wait)
            # 不可达
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


# ================================================================
# 4. 输出 schema 校验（轻量 duck typing）
# ================================================================

REQUIRED_KEYS: Dict[str, Iterable[str]] = {
    "hs_lookup_result": ("keyword", "hs_codes", "source"),
    "trade_data_result": ("hs_code", "reporter", "countries", "total_import_value_usd", "data_source"),
    "trends_result": ("keyword", "geo", "interest_over_time", "error"),
    "buyer_result": ("title", "url", "snippet", "buyer_type"),
}


def assert_shape(payload: Dict[str, Any], kind: str) -> None:
    """轻量 schema 校验：缺关键键直接抛 ResearchError。"""
    expected = REQUIRED_KEYS.get(kind, ())
    missing = [k for k in expected if k not in payload]
    if missing:
        raise ResearchError(f"{kind} payload 缺少键: {missing}")


# ================================================================
# 5. 文件缓存（避免重复 API 调用）
# ================================================================

_DEFAULT_CACHE = Path.home() / ".cache" / "hlzd-b2b-research"


def _cache_path(key: str, suffix: str = ".json") -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return _DEFAULT_CACHE / f"{digest}{suffix}"


def cache_get(key: str) -> Optional[Dict[str, Any]]:
    path = _cache_path(key)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def cache_put(key: str, payload: Dict[str, Any]) -> None:
    path = _cache_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
