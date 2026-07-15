"""hlzd-market-report: web signal collector.

从开放的 web 搜索收集候选信号。

优先级：
1. Brave Search API（如果 HLZD_BRAVE_API_KEY 环境变量存在）
2. DuckDuckGo（ddgs 包）— 兜底
3. 直接抛出 — 用户应自备

参考：b2b-overseas-market-report 已有 Brave fallback SOP。
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

LOG = lib.get_logger("collect_web")

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
DDGS_AVAILABLE = None  # lazy check


def _http_get_urllib(url: str, headers: Dict[str, str] = None, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers=headers or {
        "User-Agent": "Mozilla/5.0 (compatible; hlzd-market-report/0.1)",
        "Accept": "application/json,text/html,*/*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def collect_signals_brave(
    keywords: List[str],
    *,
    window_days: int = 30,
    max_per_keyword: int = 10,
    api_key: Optional[str] = None,
    http_get=_http_get_urllib,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """通过 Brave Search API 收集信号。

    Returns: (results, warnings)
    """
    warnings: List[str] = []
    api_key = api_key or os.environ.get("HLZD_BRAVE_API_KEY")
    if not api_key:
        warnings.append("brave_no_api_key (set HLZD_BRAVE_API_KEY or use ddgs fallback)")
        return [], warnings

    results: List[Dict[str, Any]] = []
    for kw in keywords:
        url = f"{BRAVE_ENDPOINT}?q={urllib.parse.quote(kw)}&count={max_per_keyword}"
        try:
            body = http_get(url, headers={
                "X-Subscription-Token": api_key,
                "User-Agent": "Mozilla/5.0 (compatible; hlzd-market-report/0.1)",
            })
            data = json.loads(body)
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", ""),
                    "source": "brave",
                    "query": kw,
                })
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"brave_runtime[{kw}]: {exc}")

    return results, warnings


def collect_signals_ddgs(
    keywords: List[str],
    *,
    max_per_keyword: int = 8,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """通过 DDGS（DuckDuckGo）收集信号。

    Returns: (results, warnings)
    """
    warnings: List[str] = []
    try:
        from ddgs import DDGS
    except ImportError:
        warnings.append("ddgs_not_installed (pip install ddgs)")
        return [], warnings

    results: List[Dict[str, Any]] = []
    seen: set = set()
    for kw in keywords:
        try:
            for r in DDGS().text(kw, max_results=max_per_keyword):
                url = r.get("href", "")
                if not url or url in seen:
                    continue
                seen.add(url)
                results.append({
                    "title": r.get("title", ""),
                    "url": url,
                    "snippet": r.get("body", ""),
                    "source": "ddgs",
                    "query": kw,
                })
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"ddgs_runtime[{kw}]: {exc}")

    return results, warnings


def collect_signals(
    keywords: List[str],
    *,
    window_days: int = 30,
    method: str = "auto",
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """统一入口：按 method 分派。

    method: 'auto' | 'brave' | 'ddgs'
    """
    method = method.lower().strip()
    if method == "brave":
        return collect_signals_brave(keywords, window_days=window_days)
    if method == "ddgs":
        return collect_signals_ddgs(keywords)

    # auto: brave 优先，ddgs 兜底
    results, w = collect_signals_brave(keywords, window_days=window_days)
    if not results:
        results2, w2 = collect_signals_ddgs(keywords)
        results.extend(results2)
        w.extend(w2)
    return results, w


# ================================================================
# Minimal CLI for quick testing
# ================================================================

def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="hlzd-market-report-collect")
    parser.add_argument("--keywords", "-k", nargs="+", required=True)
    parser.add_argument("--method", "-m", default="auto",
                         choices=["auto", "brave", "ddgs"])
    parser.add_argument("--output", "-o", help="Output JSON file")
    args = parser.parse_args()

    results, warnings = collect_signals(args.keywords, method=args.method)

    out = {"results": results, "warnings": warnings, "count": len(results)}
    s = json.dumps(out, ensure_ascii=False, indent=2)
    print(s)

    if args.output:
        Path(args.output).write_text(s, encoding="utf-8")
        print(f"\nwritten: {args.output}", file=sys.stderr)

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(cli())
