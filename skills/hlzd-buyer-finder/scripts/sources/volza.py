"""Volza 海关数据 adapter.

链路 A 第二阶段 + 链路 B：
- 给定 "中国供应商公司名"，返回该供应商的海外买家列表
- 用 lib.classify_volza_response 检测 blocked

Volza 免费版限制（沿用 customs-data-find SOP）：
- 每天 ~10 次搜索
- 仅返回公开字段：进口商名 / 原产国 / 数量 / 金额 / 日期
- 详细联系方式需付费
- body 长度 ≈ 11055 = blocked，> 15000 = success

设计：v0.1 不重试 blocked（用户应升级付费 / 切 ImportGenius）。
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

LOG = lib.get_logger("volza")


VOLZA_BASE_URL = "https://www.volza.com"
SEARCH_PATH = "/search"


def _http_get_urllib(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; hlzd-buyer-finder/0.1)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1", errors="replace")


def _volza_search_url(competitor_name: str, *, country_iso: Optional[str] = None) -> str:
    q = urllib.parse.quote(competitor_name)
    if country_iso:
        return f"{VOLZA_BASE_URL}{SEARCH_PATH}?q={q}&country={urllib.parse.quote(country_iso)}"
    return f"{VOLZA_BASE_URL}{SEARCH_PATH}?q={q}"


def _extract_volza_table_rows(html: str) -> List[Dict[str, Any]]:
    """极简 Volza 表格抽取（v0.1 启发式 — 公开结构可能变化）。

    Returns list of dict: { importer_name, country, origin_country, quantity, value, date }
    """
    # 找所有 tr 块
    tr_pattern = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    td_pattern = re.compile(r"<td\b[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE)
    tag_pattern = re.compile(r"<[^>]+>")

    out: List[Dict[str, Any]] = []
    for tr_m in tr_pattern.finditer(html):
        cells = tag_pattern.sub("", td_pattern.sub(r"\1", tr_m.group(1))).strip()
        # 用 ' | ' 还原结构
        # 简化：单行所有 td text 一行拿到 raw_strings
        raw_strings = [tag_pattern.sub("", m.group(1)).strip()
                       for m in td_pattern.finditer(tr_m.group(1))]
        if len(raw_strings) < 4:
            continue
        record = {
            "importer_name": raw_strings[0] if len(raw_strings) > 0 else "",
            "country": raw_strings[1] if len(raw_strings) > 1 else "",
            "origin_country": raw_strings[2] if len(raw_strings) > 2 else "",
            "quantity": raw_strings[3] if len(raw_strings) > 3 else "",
            "value": raw_strings[4] if len(raw_strings) > 4 else "",
            "date": raw_strings[5] if len(raw_strings) > 5 else "",
        }
        # basic sanity: 必须包含 importer_name 长度合理
        if 2 <= len(record["importer_name"]) <= 120 and not record["importer_name"].isdigit():
            out.append(record)
    return out


def search_volza_for_competitor(
    competitor_name: str,
    *,
    country_iso: Optional[str] = None,
    max_results: int = 10,
    http_get: Optional[Callable[[str], str]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """在 Volza 搜某供应商，找其买家。

    Returns:
        (buyers, warnings)
    """
    warnings: List[str] = []
    url = _volza_search_url(competitor_name, country_iso=country_iso)

    try:
        body = _http_get_urllib(url) if http_get is None else http_get(url)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("Volza request failed: %s", exc)
        warnings.append(f"volza_network_error: {exc}")
        return [], warnings

    body_len = len(body.encode("utf-8") if isinstance(body, str) else body)
    status = lib.classify_volza_response(body, body_len=body_len)
    if status == "blocked":
        warnings.append(
            "volza_blocked (free-tier limit; upgrade Volza Pro or use ImportGenius / 52WMB)"
        )
        return [], warnings
    if status == "loading":
        warnings.append("volza_loading_or_partial_response (network slow or anti-bot)")
        return [], warnings
    if status == "unknown" and body_len < 1000:
        warnings.append("volza_unexpected_short_response")
        return [], warnings

    # 抽取表格行
    rows = _extract_volza_table_rows(body)
    if not rows:
        warnings.append("volza_no_buyer_rows_extracted (page structure may have changed)")
        return [], warnings

    # 添加 source 字段
    out = []
    for r in rows[:max_results]:
        r["source"] = "volza.com"
        r["matched_competitor"] = competitor_name
        out.append(r)

    LOG.info("Volza: %d buyer rows for %s", len(out), competitor_name)
    return out, warnings


def search_volza_by_country(
    country_iso: str,
    product_keyword: str,
    *,
    max_results: int = 20,
    http_get: Optional[Callable[[str], str]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """链路 C：跳过竞对，按国家 + 关键词直接搜进口商。

    URL 路径：/import/{country_iso} + ?q=
    """
    warnings: List[str] = []
    path = f"/import/{country_iso.lower()}"
    url = (f"{VOLZA_BASE_URL}{path}"
           f"?SearchText={urllib.parse.quote(product_keyword)}")

    try:
        body = _http_get_urllib(url) if http_get is None else http_get(url)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"volza_network_error: {exc}")
        return [], warnings

    body_len = len(body.encode("utf-8") if isinstance(body, str) else body)
    status = lib.classify_volza_response(body, body_len=body_len)
    if status in ("blocked", "loading"):
        warnings.append(f"volza_{status}_on_keyword_search")
        return [], warnings

    rows = _extract_volza_table_rows(body)
    if not rows:
        warnings.append("volza_no_keyword_rows_extracted")
        return [], warnings

    out = []
    for r in rows[:max_results]:
        r["source"] = "volza.com"
        out.append(r)
    return out, warnings
