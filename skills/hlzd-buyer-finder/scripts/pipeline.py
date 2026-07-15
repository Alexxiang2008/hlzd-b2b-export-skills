"""hlzd-buyer-finder pipeline orchestrator.

三链路编排：
- method='auto'    : 链路 A 默认 — 阿里发现竞对 → 取前 N 供应商 → Volza 找买家
- method='competitor' : 链路 B — 用户指定竞对名（逗号分隔） → Volza 直接搜
- method='keyword' : 链路 C — 不经竞对，关键词 + 国家直接搜

输出统一 schema：
{
  "product": str,
  "country": str (iso2/3 short code like 'US'),
  "method": str,
  "competitors": [{ "company_name": str, "source": str }, ...],
  "importers": [{ "importer_name": str, "country": str, "value": str,
                  "date": str, "source": str, "matched_competitor": str? }, ...],
  "warnings": [str, ...],
  "stats": {
    "competitors_found": int,
    "importers_found_pre_dedup": int,
    "importers_after_dedup": int,
    "volza_quota_used": int,
    "alibaba_quota_used": int
  }
}
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

# 默认 rate limiter 配置（与 customs-data-find SOP 一致）
_DEFAULT_VOLZA = ("volza", 5.0, 10)        # name, min_interval_sec, daily_quota
_DEFAULT_ALIBABA = ("alibaba", 10.0, 5)


def run_auto(
    product: str,
    *,
    country_iso: Optional[str] = None,
    max_competitors: int = 5,
    max_buyers_per_competitor: int = 8,
    http_get: Optional[Callable[[str], str]] = None,
    alibaba_searcher: Optional[Callable] = None,
    volza_searcher: Optional[Callable] = None,
    volza_quota_override: Optional[Tuple[float, int]] = None,
    alibaba_quota_override: Optional[Tuple[float, int]] = None,
) -> Dict[str, Any]:
    """链路 A：阿里发现竞对 → Volza 找买家。

    所有外部 IO 均可通过 http_get / *_searcher 注入，便于测试。
    限额默认遵循 customs-data-find SOP（链接 A 每天 5 家供应商、Volza 10 次）。
    """
    if alibaba_searcher is None:
        from sources.alibaba import search_alibaba_competitors
        alibaba_searcher = lambda p: search_alibaba_competitors(
            p, max_results=max_competitors, http_get=http_get
        )
    if volza_searcher is None:
        from sources.volza import search_volza_for_competitor
        volza_searcher = lambda cn, iso: search_volza_for_competitor(
            cn, country_iso=iso, max_results=max_buyers_per_competitor, http_get=http_get
        )

    warnings: List[str] = []
    out: Dict[str, Any] = {
        "product": product,
        "country": country_iso or "",
        "method": "auto",
        "competitors": [],
        "importers": [],
        "warnings": warnings,
        "stats": {
            "competitors_found": 0,
            "importers_found_pre_dedup": 0,
            "importers_after_dedup": 0,
            "volza_quota_used": 0,
            "alibaba_quota_used": 0,
        },
    }

    # Step 1: Alibaba
    name, min_int, quota = _DEFAULT_ALIBABA
    if alibaba_quota_override:
        min_int, quota = alibaba_quota_override
    ali_lim = lib.RateLimiter(name, min_interval_sec=min_int, daily_quota=quota)

    allowed, why = ali_lim.can_call()
    if not allowed:
        warnings.append(f"alibaba_rate_limit: {why}")
        out["competitors"] = [{"company_name": product + " Co., Ltd.", "source": "manual_seed"}]
    else:
        try:
            comps, w = alibaba_searcher(product)
            warnings.extend(w)
            ali_lim.record_call()
            out["stats"]["alibaba_quota_used"] = 1
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"alibaba_runtime: {exc}")
            comps = []
        if not comps:
            warnings.append("alibaba_no_competitors_found")
            # 退路：seed 一个源自 product 名的合成供应商
            comps = [{"company_name": f"{product.title()} Co., Ltd.",
                       "source": "fallback_seed"}]
        out["competitors"] = comps
        out["stats"]["competitors_found"] = len(comps)

    # Step 2: Volza for each competitor
    name, min_int, quota = _DEFAULT_VOLZA
    if volza_quota_override:
        min_int, quota = volza_quota_override
    volza_lim = lib.RateLimiter(name, min_interval_sec=min_int, daily_quota=quota)

    all_buyers: List[Dict[str, Any]] = []
    volza_calls = 0
    for comp in out["competitors"]:
        allowed, why = volza_lim.can_call()
        if not allowed:
            warnings.append(f"volza_rate_limit (after {volza_calls} calls): {why}")
            break
        try:
            buyers, w = volza_searcher(comp["company_name"], country_iso)
            warnings.extend(w)
            volza_lim.record_call()
            volza_calls += 1
            all_buyers.extend(buyers)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"volza_runtime[{comp.get('company_name')}]: {exc}")

    out["stats"]["volza_quota_used"] = volza_calls
    out["stats"]["importers_found_pre_dedup"] = len(all_buyers)

    # Step 3: dedup
    deduped = lib.dedup_importers(all_buyers)
    out["importers"] = deduped
    out["stats"]["importers_after_dedup"] = len(deduped)

    return out


def run_competitor_list(
    competitors: List[str],
    *,
    country_iso: Optional[str] = None,
    max_buyers_per_competitor: int = 8,
    http_get: Optional[Callable[[str], str]] = None,
    volza_searcher: Optional[Callable] = None,
    volza_quota_override: Optional[Tuple[float, int]] = None,
) -> Dict[str, Any]:
    """链路 B：用户指定竞对名列表 → Volza 直接搜。"""
    from sources.volza import search_volza_for_competitor

    if volza_searcher is None:
        volza_searcher = lambda cn, iso: search_volza_for_competitor(
            cn, country_iso=iso, max_results=max_buyers_per_competitor, http_get=http_get
        )

    warnings: List[str] = []
    out: Dict[str, Any] = {
        "product": "",
        "country": country_iso or "",
        "method": "competitor",
        "competitors": [{"company_name": c, "source": "user_provided"} for c in competitors],
        "importers": [],
        "warnings": warnings,
        "stats": {
            "competitors_found": len(competitors),
            "importers_found_pre_dedup": 0,
            "importers_after_dedup": 0,
            "volza_quota_used": 0,
            "alibaba_quota_used": 0,
        },
    }

    name, min_int, quota = _DEFAULT_VOLZA
    if volza_quota_override:
        min_int, quota = volza_quota_override
    volza_lim = lib.RateLimiter(name, min_interval_sec=min_int, daily_quota=quota)

    all_buyers: List[Dict[str, Any]] = []
    volza_calls = 0
    for comp_name in competitors:
        allowed, why = volza_lim.can_call()
        if not allowed:
            warnings.append(f"volza_rate_limit (after {volza_calls} calls): {why}")
            break
        try:
            buyers, w = volza_searcher(comp_name, country_iso)
            warnings.extend(w)
            volza_lim.record_call()
            volza_calls += 1
            all_buyers.extend(buyers)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"volza_runtime[{comp_name}]: {exc}")

    out["stats"]["volza_quota_used"] = volza_calls
    out["stats"]["importers_found_pre_dedup"] = len(all_buyers)
    deduped = lib.dedup_importers(all_buyers)
    out["importers"] = deduped
    out["stats"]["importers_after_dedup"] = len(deduped)
    return out


def run_keyword(
    product: str,
    country_iso: str,
    *,
    max_results: int = 20,
    http_get: Optional[Callable[[str], str]] = None,
    keyword_searcher: Optional[Callable] = None,
    volza_searcher: Optional[Callable] = None,
) -> Dict[str, Any]:
    """链路 C：跳过竞对，关键词 + 国家直接搜。"""
    from sources.keyword import search_keyword_public
    from sources.volza import search_volza_by_country

    if keyword_searcher is None:
        keyword_searcher = lambda p, c: search_keyword_public(p, c, max_results=max_results, http_get=http_get)
    if volza_searcher is None:
        volza_searcher = lambda c, p: search_volza_by_country(c, p, max_results=max_results, http_get=http_get)

    warnings: List[str] = []
    all_buyers: List[Dict[str, Any]] = []

    # 先 Volza 关键词搜
    try:
        buyers_v, wv = volza_searcher(country_iso, product)
        warnings.extend(wv)
        all_buyers.extend(buyers_v)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"volza_keyword_runtime: {exc}")

    # 再 public directory 兜底
    try:
        buyers_k, wk = keyword_searcher(product, country_iso)
        warnings.extend(wk)
        all_buyers.extend(buyers_k)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"keyword_runtime: {exc}")

    out = {
        "product": product,
        "country": country_iso,
        "method": "keyword",
        "competitors": [],
        "importers": lib.dedup_importers(all_buyers),
        "warnings": warnings,
        "stats": {
            "competitors_found": 0,
            "importers_found_pre_dedup": len(all_buyers),
            "importers_after_dedup": len(lib.dedup_importers(all_buyers)),
            "volza_quota_used": 1,
            "alibaba_quota_used": 0,
        },
    }
    return out


def run_pipeline(
    product: str,
    *,
    method: str = "auto",
    country_iso: Optional[str] = None,
    competitors: Optional[List[str]] = None,
    max_competitors: int = 5,
    max_buyers_per_competitor: int = 8,
    http_get: Optional[Callable[[str], str]] = None,
    volza_quota_override: Optional[Tuple[float, int]] = None,
    alibaba_quota_override: Optional[Tuple[float, int]] = None,
    alibaba_searcher: Optional[Callable] = None,
    volza_searcher: Optional[Callable] = None,
) -> Dict[str, Any]:
    """统一入口：按 method 分派到对应链。

    透传 quota overrides 与 searchers — 主要供测试注入 mock。
    """
    method = method.lower().strip()
    if method == "auto":
        return run_auto(
            product,
            country_iso=country_iso,
            max_competitors=max_competitors,
            max_buyers_per_competitor=max_buyers_per_competitor,
            http_get=http_get,
            volza_quota_override=volza_quota_override,
            alibaba_quota_override=alibaba_quota_override,
            alibaba_searcher=alibaba_searcher,
            volza_searcher=volza_searcher,
        )
    if method == "competitor":
        if not competitors:
            raise lib.InvalidParameterError(
                "--competitor is required when --method=competitor"
            )
        return run_competitor_list(
            competitors,
            country_iso=country_iso,
            max_buyers_per_competitor=max_buyers_per_competitor,
            http_get=http_get,
            volza_quota_override=volza_quota_override,
            volza_searcher=volza_searcher,
        )
    if method == "keyword":
        if not country_iso:
            raise lib.InvalidParameterError("--country is required when --method=keyword")
        return run_keyword(
            product,
            country_iso,
            max_results=max_buyers_per_competitor * max_competitors,
            http_get=http_get,
            keyword_searcher=None,
            volza_searcher=volza_searcher,
        )
    raise lib.InvalidParameterError(f"unknown method: {method!r}")
