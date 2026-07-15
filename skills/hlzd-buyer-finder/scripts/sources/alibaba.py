"""Alibaba 自动化发现竞对 (链路 A 第一阶段).

从 Alibaba 国际站搜索结果抽取出"中国供应商公司名"候选。

设计：
- 不依赖 Playwright（v0.1 用 urllib）
- 若被反爬 / captcha，warning "alibaba_blocked" 并返回空
- 公司名抽取用 deterministic regex + lib.extract_company_candidates_from_text
- 接受 `http_get` 注入，便于测试
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lib  # noqa: E402

LOG = lib.get_logger("alibaba")


# Alibaba 搜索 URL（公开）
ALIBABA_SEARCH_URL = "https://www.alibaba.com/trade/search"


def _http_get_urllib(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; hlzd-buyer-finder/0.1; +https://hlzd.example.com)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        # 大多数返回 utf-8
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1", errors="replace")


def search_alibaba_competitors(
    product: str,
    *,
    max_results: int = 15,
    http_get: Optional[Callable[[str], str]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """从 Alibaba 搜索结果抽取中国供应商公司名。

    Returns:
        (companies, warnings) where each company is
            { "company_name": ..., "source": "alibaba.com" }
    """
    warnings: List[str] = []
    url = f"{ALIBABA_SEARCH_URL}?SearchText={urllib.parse.quote(product)}"

    try:
        body = _http_get_urllib(url) if http_get is None else http_get(url)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("Alibaba request failed: %s", exc)
        warnings.append(f"alibaba_network_error: {exc}")
        return [], warnings

    if not body or len(body) < 1000:
        warnings.append("alibaba_empty_response (possibly captcha or bot block)")
        return [], warnings

    # captcha / verify 快速判断
    lc = body.lower()
    if any(s in lc for s in ["captcha", "robot check", "verify you are human", "slider"]):
        warnings.append("alibaba_captcha_triggered (recommend manual login or use Volza directly)")
        return [], warnings

    candidates = lib.extract_company_candidates_from_text(body)
    if not candidates:
        warnings.append("alibaba_no_companies_extracted (page structure may have changed)")
        return [], warnings

    companies = []
    for c in candidates[:max_results]:
        companies.append({"company_name": c, "source": "alibaba.com"})
    LOG.info("Alibaba: %d candidate companies", len(companies))
    return companies, warnings
