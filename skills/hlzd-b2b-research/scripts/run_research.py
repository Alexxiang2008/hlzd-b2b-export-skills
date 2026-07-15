#!/usr/bin/env python3
"""hlzd-b2b-research pipeline orchestrator.

一站式 B2B 工业品海外调研：
  Step 1: HS 编码候选 (hs_lookup.py)
  Step 2: UN Comtrade 市场规模 (trade_data.py)
  Step 3: Google Trends 需求热度 (keyword_trends.py)
  Step 4: DDGS 买家线索 (buyer_search.py)

用法:
  py scripts/run_research.py --product "OCTG casing" --markets "UAE Saudi" \\
                              --hs-candidate 730429 --output report.md
  py scripts/run_research.py --product "container house" --markets "Australia Africa" \\
                              --delay 4 --skip-trends
  py scripts/run_research.py --product "petrochemical pipe" --markets "US" \\
                              --output-json report.json --output-md report.md

外部依赖（与子脚本一致）：
- playwright + chromium: HS 编码查询
- comtradeapicall: 贸易数据
- pytrends: 关键词热度
- ddgs: 买家搜索

如未安装对应依赖，对应 Step 会被 skip（不中断），错误记入 result['warnings']。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# 让脚本可作为模块导入（也作为 entry point）
sys.path.insert(0, str(Path(__file__).parent))
import lib  # noqa: E402

LOG = lib.get_logger("run_research")

# 国家简称 → ISO3 / UN Comtrade 码（与 trade_data.py 同步）
COUNTRY_HINTS: Dict[str, Dict[str, str]] = {
    "uae": {"iso3": "ARE", "comtrade": "784", "trends_geo": "AE"},
    "united arab emirates": {"iso3": "ARE", "comtrade": "784", "trends_geo": "AE"},
    "saudi": {"iso3": "SAU", "comtrade": "682", "trends_geo": "SA"},
    "saudi arabia": {"iso3": "SAU", "comtrade": "682", "trends_geo": "SA"},
    "us": {"iso3": "USA", "comtrade": "842", "trends_geo": "US"},
    "usa": {"iso3": "USA", "comtrade": "842", "trends_geo": "US"},
    "nigeria": {"iso3": "NGA", "comtrade": "566", "trends_geo": "NG"},
    "australia": {"iso3": "AUS", "comtrade": "036", "trends_geo": "AU"},
    "south africa": {"iso3": "ZAF", "comtrade": "710", "trends_geo": "ZA"},
    "india": {"iso3": "IND", "comtrade": "699", "trends_geo": "IN"},
    "brazil": {"iso3": "BRA", "comtrade": "076", "trends_geo": "BR"},
}


# ================================================================
# 1. Step adapters — 调子脚本的导入
# ================================================================

def _step_hs_lookup(product: str, top_n: int = 5) -> Dict[str, Any]:
    """调用 hs_lookup 的函数。返回 dict；若失败返回 {'error': ...}。"""
    try:
        import hs_lookup  # type: ignore[import-not-found]
        results = hs_lookup.lookup_hs_code(product, max_pages=2, timeout=12000)
        return {
            "keyword": product,
            "source": "hsbianma.com",
            "total_results": len(results),
            "hs_codes": results[:top_n],
        }
    except ImportError as exc:
        return {"keyword": product, "source": "hsbianma.com",
                "hs_codes": [], "error": f"playwright 未安装: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"keyword": product, "source": "hsbianma.com",
                "hs_codes": [], "error": str(exc)}


def _step_trade_data(hs_code: str, reporter_code: str, period: str) -> Dict[str, Any]:
    """调用 trade_data 的函数。"""
    try:
        import trade_data  # type: ignore[import-not-found]
        import pandas as pd  # type: ignore[import-not-found]
        df = trade_data.get_market_data(hs_code, reporter_code, period=period, max_records=200)
        return trade_data.export_json(df, hs_code, reporter_code)
    except ImportError as exc:
        return {"hs_code": hs_code, "reporter": reporter_code,
                "countries": [], "total_import_value_usd": 0,
                "data_source": "UN Comtrade", "error": f"comtradeapicall/pandas 未安装: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"hs_code": hs_code, "reporter": reporter_code,
                "countries": [], "total_import_value_usd": 0,
                "data_source": "UN Comtrade", "error": str(exc)}


def _step_trends(keyword: str, geo: str, delay: int) -> Dict[str, Any]:
    """调用 keyword_trends 的函数。"""
    try:
        import keyword_trends  # type: ignore[import-not-found]
        results = keyword_trends.fetch_multiple_keywords([keyword], geo=geo, delay=delay)
        return results[0] if results else {"keyword": keyword, "geo": geo,
                                            "interest_over_time": None, "related_queries": [],
                                            "interest_by_region": None, "error": "no result"}
    except ImportError as exc:
        return {"keyword": keyword, "geo": geo, "interest_over_time": None,
                "related_queries": [], "interest_by_region": None,
                "error": f"pytrends 未安装: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"keyword": keyword, "geo": geo, "interest_over_time": None,
                "related_queries": [], "interest_by_region": None,
                "error": str(exc)}


def _step_buyer_search(product: str, market: str, max_results: int, delay: int,
                        include_tenders: bool = True) -> Dict[str, Any]:
    """调用 buyer_search 的函数。"""
    try:
        import buyer_search  # type: ignore[import-not-found]
        markets = market.split() if market else []
        per_market = max(5, max_results // max(len(markets), 1) + 3) if markets else max_results
        buyers = []
        if markets:
            for m in markets:
                b = buyer_search.search_buyers([product], m, per_market, delay)
                buyers.extend(b)
        else:
            buyers = buyer_search.search_buyers([product], None, max_results, delay)
        # 去重
        seen = set()
        unique = []
        for b in buyers:
            if b["url"] not in seen:
                seen.add(b["url"])
                unique.append(b)
        tenders = []
        if include_tenders:
            try:
                tenders = buyer_search.search_procurement_tenders([product], market, 10, delay)
            except Exception:  # noqa: BLE001
                tenders = []
        return {
            "total_buyers": len(unique),
            "total_tenders": len(tenders),
            "buyers": unique[:max_results],
            "tenders": tenders,
        }
    except ImportError as exc:
        return {"total_buyers": 0, "total_tenders": 0, "buyers": [], "tenders": [],
                "error": f"ddgs 未安装: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"total_buyers": 0, "total_tenders": 0, "buyers": [], "tenders": [],
                "error": str(exc)}


# ================================================================
# 2. Pipeline main
# ================================================================

def run_pipeline(
    product: str,
    markets: List[str],
    hs_candidate: Optional[str] = None,
    period: str = "2023",
    delay: int = 12,
    skip_trends: bool = False,
    skip_buyers: bool = False,
    include_tenders: bool = True,
    max_buyers: int = 20,
) -> Dict[str, Any]:
    """跑完整 4 步 pipeline。

    Returns:
      dict with keys:
        - product: 查询产品名
        - markets: 目标市场列表
        - hs_code_candidates: HS 编码候选
        - trade_data: {reporter -> Comtrade 数据}
        - trends: {reporter -> 趋势}
        - buyers: {reporter -> 买家}
        - warnings: list of skip reason
    """
    warnings: List[str] = []
    out: Dict[str, Any] = {
        "product": product,
        "markets": markets,
        "hs_code_candidates": [],
        "trade_data": {},
        "trends": {},
        "buyers": {},
        "warnings": warnings,
    }

    # Step 1: HS 编码
    LOG.info("Step 1/4: HS 编码查询 ...")
    hs_res = _step_hs_lookup(product)
    out["hs_code_candidates"] = hs_res.get("hs_codes", [])
    if "error" in hs_res:
        warnings.append(f"[hs_lookup] {hs_res['error']}")
        LOG.warning("HS 查询失败（向后兼容）: %s", hs_res["error"])
    if hs_candidate is None and out["hs_code_candidates"]:
        first = out["hs_code_candidates"][0].get("hs_code", "")
        first = re.sub(r"\D", "", first)[:6]
        hs_candidate = first or None
    out["hs_code_used"] = hs_candidate

    if not markets:
        markets = ["us"]  # 默认一个 fallback

    # Step 2/3/4: 逐市场循环
    for market in markets:
        key = market.lower()
        hint = COUNTRY_HINTS.get(key, {"iso3": market.upper(), "comtrade": market.lower()})
        reporter_code = hint["comtrade"] if "comtrade" in hint else market
        trends_geo = hint.get("trends_geo", "")
        LOG.info("[%s] Step 2: Comtrade (hs=%s reporter=%s)", market, hs_candidate, reporter_code)
        if hs_candidate:
            out["trade_data"][market] = _step_trade_data(hs_candidate, reporter_code, period)
            if "error" in out["trade_data"][market]:
                warnings.append(f"[trade_data:{market}] {out['trade_data'][market]['error']}")
        else:
            warnings.append(f"[trade_data:{market}] skip: 无 HS 编码")
            out["trade_data"][market] = {"error": "no hs_code"}

        if not skip_trends:
            LOG.info("[%s] Step 3: Google Trends (geo=%s)", market, trends_geo)
            out["trends"][market] = _step_trends(product, trends_geo, delay)
            if "error" in out["trends"][market]:
                warnings.append(f"[trends:{market}] {out['trends'][market]['error']}")
        else:
            out["trends"][market] = {"skipped": True}

        if not skip_buyers:
            LOG.info("[%s] Step 4: Buyer search (include_tenders=%s)", market, include_tenders)
            out["buyers"][market] = _step_buyer_search(product, market, max_buyers, delay, include_tenders)
            if "error" in out["buyers"][market]:
                warnings.append(f"[buyers:{market}] {out['buyers'][market]['error']}")
        else:
            out["buyers"][market] = {"skipped": True}

    return out


# ================================================================
# 3. Markdown 报告生成
# ================================================================

def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# {report['product']} B2B 海外市场调研报告",
        "",
        f"- 目标市场: {', '.join(report['markets'])}",
        f"- 使用 HS 编码: {report.get('hs_code_used') or '未识别'}",
        f"- 警告 (skip 原因): {len(report.get('warnings', []))}",
        "",
        "## 一、HS 编码候选",
    ]
    for c in report.get("hs_code_candidates", []):
        lines.append(f"- `{c.get('hs_code', '?')}` {c.get('name', '')[:30]} "
                     f"退税率:{c.get('rebate', '-')}% 监管:{c.get('regulation', '-')}")
    if not report.get("hs_code_candidates"):
        lines.append("- 未识别 HS 编码（建议手动补查 hsbianma.com）")

    lines += ["", "## 二、市场规模（UN Comtrade）"]
    for market, data in report.get("trade_data", {}).items():
        if data.get("skipped") or not data:
            lines.append(f"\n### {market}")
            lines.append("- skipped")
            continue
        if "error" in data and not data.get("countries"):
            lines.append(f"\n### {market}\n- error: {data['error']}")
            continue
        total = data.get("total_import_value_usd", 0)
        lines.append(f"\n### {market} (HS {data.get('hs_code', '?')})")
        lines.append(f"- 进口总额: ${total/1e6:.1f}M USD")
        top = data.get("countries", [])[:5]
        for c in top:
            lines.append(f"  - {c.get('country', '?')}: ${c.get('import_value_usd', 0)/1e6:.1f}M "
                         f"({c.get('share_pct', 0):.1f}%)")

    lines += ["", "## 三、需求热度（Google Trends）"]
    for market, data in report.get("trends", {}).items():
        if data.get("skipped"):
            lines.append(f"\n### {market}\n- skipped")
            continue
        if data.get("error"):
            lines.append(f"\n### {market}\n- error: {data['error']}")
            continue
        lines.append(f"\n### {market} ({data.get('geo', 'N/A')})")
        iot = data.get("interest_over_time")
        if iot:
            try:
                series = next(iter(iot.values()))
                nums = [v for v in series.values() if isinstance(v, (int, float))]
                if nums:
                    lines.append(f"- 平均热度: {sum(nums)/len(nums):.1f} | 峰值: {max(nums):.0f} | 低值: {min(nums):.0f}")
            except Exception:
                pass
        rq = data.get("related_queries", [])
        if rq:
            lines.append(f"- 相关上升词: {', '.join(it.get('query', '') for it in rq[:5])}")

    lines += ["", "## 四、买家线索 + 招标信息"]
    for market, data in report.get("buyers", {}).items():
        if data.get("skipped"):
            lines.append(f"\n### {market}\n- skipped")
            continue
        if "error" in data and data.get("total_buyers", 0) == 0:
            lines.append(f"\n### {market}\n- error: {data['error']}")
            continue
        lines.append(f"\n### {market} (共 {data.get('total_buyers', 0)} 条买家，{data.get('total_tenders', 0)} 条招标)")
        # 按 buyer_type 分组
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for b in data.get("buyers", []):
            by_type.setdefault(b.get("buyer_type", "其他"), []).append(b)
        for buyer_type, items in sorted(by_type.items(), key=lambda x: -len(x[1]))[:5]:
            lines.append(f"\n#### 【{buyer_type}】({len(items)} 条)")
            for it in items[:3]:
                lines.append(f"- {it.get('title', '')[:70]}")
                lines.append(f"  → {it.get('url', '')}")
        if data.get("tenders"):
            lines.append(f"\n#### 招标 (前 5 条)")
            for t in data["tenders"][:5]:
                lines.append(f"- {t.get('title', '')[:70]}")
                lines.append(f"  → {t.get('url', '')}")

    if report.get("warnings"):
        lines += ["", "## ⚠️ Warnings"]
        for w in report["warnings"]:
            lines.append(f"- {w}")

    return "\n".join(lines) + "\n"


# ================================================================
# 4. CLI
# ================================================================

def _split_csv(value: str) -> List[str]:
    return [s.strip() for s in re.split(r"[,\s]+", value) if s.strip()]


def cli() -> int:
    parser = argparse.ArgumentParser(
        prog="hlzd-b2b-research",
        description="Pipeline 4-step B2B industrial research (HS code → market size → trends → buyers)",
    )
    parser.add_argument("--product", required=True, help="产品关键词（英文/中文均可）")
    parser.add_argument("--markets", help="目标市场（空格或逗号分隔，如 'UAE Saudi US'）")
    parser.add_argument("--hs-candidate", help="直接指定 HS 编码（6位），跳过 hsbianma.com 自动查询")
    parser.add_argument("--period", default="2023", help="UN Comtrade 年份，默认 2023")
    parser.add_argument("--delay", type=int, default=12, help="趋势/买家 查询间隔秒（防429）")
    parser.add_argument("--max-buyers", type=int, default=20, help="单市场最多买家数")
    parser.add_argument("--skip-trends", action="store_true", help="跳过 Trends")
    parser.add_argument("--skip-buyers", action="store_true", help="跳过买家搜索")
    parser.add_argument("--no-tenders", action="store_true", help="不搜索招标信息")
    parser.add_argument("--output-json", help="JSON 报告输出路径")
    parser.add_argument("--output-md", help="Markdown 报告输出路径")
    parser.add_argument("--pretty", action="store_true", help="JSON pretty print")

    args = parser.parse_args()
    markets = _split_csv(args.markets) if args.markets else ["us"]

    LOG.info("Pipeline 启动: product=%s markets=%s", args.product, markets)

    report = run_pipeline(
        product=args.product,
        markets=markets,
        hs_candidate=args.hs_candidate,
        period=args.period,
        delay=args.delay,
        skip_trends=args.skip_trends,
        skip_buyers=args.skip_buyers,
        include_tenders=not args.no_tenders,
        max_buyers=args.max_buyers,
    )

    md = render_markdown(report)

    if args.output_md:
        Path(args.output_md).write_text(md, encoding="utf-8")
        LOG.info("Markdown 报告已保存: %s", args.output_md)

    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None),
            encoding="utf-8",
        )
        LOG.info("JSON 报告已保存: %s", args.output_json)

    # 默认 stdout 输出 JSON
    out = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
