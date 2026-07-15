"""关键词回退源 —— 当阿里 + Volza 都被屏蔽时，使用 DDGS 等开放搜索。

链路 C：用户给产品关键词 + 国家，从搜索引擎（DDGS）+ 公司目录类站点找
公开列出的进口商。

注：真正的 DDGS 实现在二期接入，v0.1 仅提供 schema + 占位实现 + keyword 抽取。
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lib  # noqa: E402

LOG = lib.get_logger("keyword")


# 已知进口商 / 行业目录（公开且 robots 友好）
PUBLIC_IMPORTER_DIR_URLS: Dict[str, str] = {
    "us": "https://www.importgenius.com/us-importers",
    "uk": "https://www.importgenius.com/uk-importers",
    # 其它国家 v0.1 占位
}


def _heuristic_extract_company(text: str) -> List[Dict[str, Any]]:
    """从自由文本中抓看起来像公司名 + 国家短语的行。"""
    candidates: List[Dict[str, Any]] = []
    seen: Dict[str, None] = {}
    for line in text.splitlines():
        clean = line.strip()
        if len(clean) < 4 or len(clean) > 120:
            continue
        low = clean.lower()
        if any(ind in low for ind in lib.CN_COMPANY_INDICATORS):
            if clean in seen:
                continue
            seen[clean] = None
            candidates.append({"importer_name": clean[:80], "source": "public_directory"})
    return candidates


def search_keyword_public(
    product: str,
    country_iso: str,
    *,
    max_results: int = 20,
    http_get: Optional[Callable[[str], str]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """v0.1 占位实现：用通用规则 + （可选）DDGS。"""
    warnings: List[str] = []
    url = PUBLIC_IMPORTER_DIR_URLS.get(country_iso.lower())
    if url is None:
        warnings.append(f"keyword_source_no_public_dir_for_country={country_iso}")
        return [], warnings

    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; hlzd-buyer-finder/0.1)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"keyword_network_error: {exc}")
        return [], warnings

    rows = _heuristic_extract_company(body)
    for r in rows[:max_results]:
        r["country"] = country_iso.upper()
        r["value"] = ""
    if not rows:
        warnings.append("keyword_no_results")
    return rows[:max_results], warnings
