"""hlzd-customer-due-diligence shared library.

- 日志
- 错误归类
- 制裁粗筛（国家 + 实体 + dual-use）→ 在 v0.1.1 改为调用 hlzd-trade-compliance
- 5 维评分引擎
- Schema validation
- 同名公司 dedup
- 输出 schema 强校验
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ================================================================
# 1. 日志
# ================================================================

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-customer-due-diligence") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# 0.5 Trade Compliance Bridge (W8 integration)
# ================================================================
#
# diligence v0.1.0 用 20 行 OFAC 静态子集做合规粗筛。
# W8 hlzd-trade-compliance 上线后, 这个 Skill 用作合规护栏
# 的 source-of-truth —— diligence 不再 hardcode 制裁表。
#
# 此处动态 import trade-compliance/scripts；失败时降级到本地
# inline 列表（向后兼容 + 离线可用）。

_TC_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "hlzd-trade-compliance" / "scripts"
_tc_check = None
_TC_BRIDGE_LOG = get_logger("hlzd-customer-due-diligence.tc_bridge")


def _try_load_trade_compliance_logging_helpers():
    """Logging initializer placed early (auto-redirects when called lazily)."""
    return _try_load_trade_compliance()


def _try_load_trade_compliance():
    """动态 import trade-compliance/scripts 的 check 模块。

    严格按依赖顺序: sources/__init__  -> sources/ofac_sdn etc -> check.
    """
    global _tc_check
    if _tc_check is not None:
        return _tc_check
    if not _TC_SCRIPTS.exists():
        return None
    try:
        sys.path.insert(0, str(_TC_SCRIPTS))

        # 1) load trade-compliance lib (top-level)
        lib_spec = importlib.util.spec_from_file_location(
            "_hlzd_tc_lib", str(_TC_SCRIPTS / "lib.py"))
        lib_mod = importlib.util.module_from_spec(lib_spec)
        sys.modules["_hlzd_tc_lib"] = lib_mod
        lib_spec.loader.exec_module(lib_mod)

        # 2) load sources package + each adapter
        sources_dir = _TC_SCRIPTS / "sources"
        sys.path.insert(0, str(sources_dir))
        from importlib.machinery import SourceFileLoader
        spec_pkg = importlib.util.spec_from_file_location(
            "_hlzd_tc_sources", str(sources_dir / "__init__.py"))
        sources_pkg = importlib.util.module_from_spec(spec_pkg)
        sys.modules["_hlzd_tc_sources"] = sources_pkg
        spec_pkg.loader.exec_module(sources_pkg)
        for f in ("ofac_sdn", "eu_consolidated", "bis_entity",
                  "country_embargo", "dual_use"):
            f_spec = importlib.util.spec_from_file_location(
                f"_hlzd_tc_sources.{f}", str(sources_dir / f"{f}.py"))
            f_mod = importlib.util.module_from_spec(f_spec)
            sys.modules[f"_hlzd_tc_sources.{f}"] = f_mod
            f_spec.loader.exec_module(f_mod)

        # 3) make 'lib' alias visible to check.py imports
        sys.modules["lib"] = lib_mod

        # 4) load check.py — it does `import lib` and `from sources import (...)`
        chk_spec = importlib.util.spec_from_file_location(
            "_hlzd_tc_check", str(_TC_SCRIPTS / "check.py"))
        chk_mod = importlib.util.module_from_spec(chk_spec)
        sys.modules["_hlzd_tc_check"] = chk_mod
        chk_spec.loader.exec_module(chk_mod)

        _tc_check = chk_mod
        return _tc_check
    except Exception as exc:
        _TC_BRIDGE_LOG.warning("trade-compliance bridge load failed: %s", exc)
        return None


def compliance_clearance_via_trade_compliance(
    buyer_name: str, buyer_country: str, product: str = ""
) -> Optional[Dict[str, Any]]:
    """调用 hlzd-trade-compliance.run_compliance_check。

    Returns dict {clearance, violations[], passed} 或 None（TC 未加载）。
    """
    tc = _try_load_trade_compliance()
    if tc is None:
        return None
    try:
        tx = {
            "buyer_name": buyer_name,
            "buyer_country": buyer_country,
            "product": product or "industrial equipment",
        }
        cr = tc.run_compliance_check(tx)
        d = cr.to_dict()
        violations = []
        for chk in d.get("check_results", []):
            for f in chk.get("flags", []):
                violations.append({
                    "rule_id": f.get("rule_id"),
                    "severity": f.get("severity"),
                    "source": f.get("source"),
                    "evidence": f.get("evidence"),
                })
        return {
            "clearance": d.get("clearance"),
            "violations": violations,
            "passed": d.get("clearance") == "CLEARED",
            "rationale": d.get("rationale"),
        }
    except Exception:
        return None


# ================================================================
# 2. 错误归类
# ================================================================

class DiligenceError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-customer-due-diligence",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        return {"error_class": self.__class__.__name__,
                "message": str(self), "source": self.source,
                "recoverable": self.recoverable}


class ComplianceViolation(DiligenceError):
    """Hit a sanctioned country / entity / dual-use — output must flag."""
    def __init__(self, message: str):
        super().__init__(message, source="compliance", recoverable=True)


class InvalidBuyerRecord(DiligenceError):
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


# ================================================================
# 3. 制裁粗筛（复用自 hlzd-inquiry-qualify + 扩展）
# ================================================================

# 制裁国家（保守静态列表）
SANCTIONED_COUNTRIES: set = {
    "north korea", "dprk",
    "iran",
    "syria",
    "cuba",
    "crimea", "donetsk", "luhansk", "sevastopol",
}

# Dual-use / 敏感品类（仅粗筛标志）
DUAL_USE_TERMS: List[str] = [
    "dual-use", "dual use", "two-use", "two use",
    "encryption module", "high-strength steel beyond 1500 MPa",
    "maraging steel 350", "OCTG for re-export",
]

# OFAC SDN 静态子集（v0.1 — 仅高频 30 个；正式版接 OFAC SDN API 每 24h 拉取）
OFAC_SDN_STATIC_NAMES: List[str] = [
    "Russian National Commercial Bank",
    "Bank Saderat Iran",
    "Hezbollah",
    "Hamas",
    "Islamic State of Iraq and the Levant",
    "Wagner Group",
    "Tornado Cash",
    "Lazarus Group",
    "Fancy Bear",
    "Cozy Bear",
    "Pyongyang University of Science and Technology",
    "Iran Aircraft Manufacturing Industrial Co",
    "Tanker Pacific",
    "Islamic Revolutionary Guard Corps",
    "Navalny Anticorruption Foundation",
    "Al-Shabaab",
    "Boko Haram",
    "Taliban",
    "Donetsk People's Republic",
    "Luhansk People's Republic",
]

# 欺诈高危信号
FRAUD_RISK_TERMS: List[str] = [
    "advance payment to personal account",
    "western union payment only",
    "money gram",
    "send to personal account",
    "100% advance",
    "worldremit only",
]


# ================================================================
# 4. 公司名 / 国家 dedup helpers
# ================================================================

def normalize_company(name: str) -> str:
    """简化归一：lowercase + 去除标点。None 输入返回空串。"""
    if not name:
        return ""
    s = name.strip().lower()
    s = re.sub(r"[.,\s]+", " ", s).strip()
    for suf in ("co ltd", "co ltd.", "co., ltd.", "co.,ltd.", "co. ltd.",
                 "limited", "ltd.", "ltd", "llc", "inc.", "inc",
                 "corp.", "corp", "corporation", "gmbh",
                 "s.a.", "s.a", "s.l.", "company", "co.", "co"):
        s = re.sub(rf"\s+{re.escape(suf)}\s*$", "", s)
    return s[:80]


def is_sanctioned_country(country: str) -> bool:
    if not country:
        return False
    return any(sc in country.lower() for sc in SANCTIONED_COUNTRIES)


def is_sanctioned_entity(name: str, snippet: str = "") -> bool:
    """模糊匹配 OFAC SDN 静态名（大小写不敏感）。"""
    text = " ".join([name or "", snippet or ""]).lower()
    return any(sdn.lower() in text for sdn in OFAC_SDN_STATIC_NAMES)


def has_dual_use_term(text: str) -> bool:
    lc = text.lower()
    return any(t.lower() in lc for t in DUAL_USE_TERMS)


def has_fraud_term(text: str) -> List[str]:
    lc = text.lower()
    return [t for t in FRAUD_RISK_TERMS if t.lower() in lc]


# ================================================================
# 5. Schema validation
# ================================================================

REQUIRED_BUYER_FIELDS = ("importer_name", "country")
REQUIRED_RECORD_FIELDS = ("importer_name", "country", "company_score",
                            "company_grade", "compliance", "recommendation")


def assert_buyer_shape(buyer: Dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_BUYER_FIELDS if k not in buyer or not buyer.get(k)]
    if missing:
        raise InvalidBuyerRecord(f"buyer missing required fields: {missing}")


# ================================================================
# 6. 5 维评分引擎
# ================================================================

# 维度满分：D1=25, D2=25, D3=15, D4=20, D5=15 → 100
GRADE_THRESHOLDS = [
    (90, "A", "Strong buyer. Recommend priority outreach within 24h."),
    (70, "B", "Solid buyer. Outreach within 48h; supplement missing fields."),
    (50, "C", "Marginal. Nurture pool; re-evaluate in 90 days."),
    (0,  "D", "Low quality / non-actionable. Auto-template or archive."),
]

CUSTOMER_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "Manufacturer": ["manufacturing", "factory", "industrial plant", "production"],
    "Distributor": ["distributor", "wholesale", "importer"],
    "EPC": ["EPC", "engineering procurement", "contractor", "turnkey", "construction"],
    "OEM": ["OEM", "original equipment manufacturer", "white-label", "private label"],
    "End User": ["operator", "end user", "mining operator", "oilfield operator"],
    "Trader": ["trader", "trading company", "import export", "broker"],
}


def detect_customer_type(text: str) -> str:
    """根据 text（含 snippet / about）判 buyer 类型。"""
    lc = text.lower()
    for ctype, keys in CUSTOMER_TYPE_KEYWORDS.items():
        if any(k.lower() in lc for k in keys):
            return ctype
    return "Unknown"


def score_dimensional(buyer: Dict[str, Any]) -> Dict[str, Any]:
    """5 维评分：D1 公司真实性 25 / D2 公司实力 25 / D3 客户类型 15
    / D4 采购能力 20 / D5 风险评估 15
    """
    text_blob = " ".join(filter(None, [
        buyer.get("importer_name", ""), buyer.get("country", ""),
        buyer.get("snippet", ""), buyer.get("contact_email", ""),
        buyer.get("linkedin", ""), buyer.get("website", ""),
    ]))

    # ---- D1 公司真实性 ----
    d1 = 0
    missing_d1 = []
    if buyer.get("importer_name"):
        d1 += 5
    else:
        missing_d1.append("importer_name")
    # email
    email = buyer.get("contact_email") or ""
    if email:
        free_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                         "qq.com", "163.com", "126.com"}
        domain = email.split("@")[-1].lower() if "@" in email else ""
        d1 += 5 if domain in free_domains else 12
    else:
        missing_d1.append("contact_email")
    # LinkedIn
    if buyer.get("linkedin"):
        d1 += 8
    else:
        missing_d1.append("linkedin")
    d1 = min(d1, 25)

    # ---- D2 公司实力 ----
    d2 = 0
    missing_d2 = []
    snippet = buyer.get("snippet", "")
    has_size_signal = bool(re.search(r"\b\d{2,}\s*(?:employees|staff|workers|people)\b",
                                      snippet.lower()))
    has_revenue_signal = bool(re.search(r"\b(?:revenue|turnover|USD|EUR)\b", snippet.lower()))
    has_industry = bool(re.search(r"\bindustry\b|\bmarket leader\b|\bmanufacturer\b", snippet.lower()))
    if has_size_signal:
        d2 += 10
    else:
        missing_d2.append("company_size")
    if has_revenue_signal:
        d2 += 10
    else:
        missing_d2.append("revenue_indicator")
    if has_industry:
        d2 += 5
    else:
        missing_d2.append("industry_signal")
    d2 = min(d2, 25)

    # ---- D3 客户类型 ----
    ctype = detect_customer_type(text_blob)
    high_quality_types = {"Manufacturer", "EPC", "End User", "OEM"}
    med_types = {"Distributor"}
    low_types = {"Trader", "Unknown"}
    if ctype in high_quality_types:
        d3 = 15
    elif ctype == "Distributor":
        d3 = 10
    elif ctype == "Trader":
        d3 = 5
    else:
        d3 = 0
    missing_d3 = [] if ctype != "Unknown" else ["customer_type_signal"]

    # ---- D4 采购能力 ----
    d4 = 0
    missing_d4 = []
    # Volza 数据是天然历史进口信号；本 Skill 接受 buyer 带 usd_history / qty_history
    if buyer.get("usd_history") or buyer.get("qty_history"):
        d4 += 15
    else:
        missing_d4.append("historical_imports")
    # 项目经验
    if re.search(r"\b(tender|EPC|project|pharma|mining|oilfield)\b", snippet.lower()):
        d4 += 5
    else:
        missing_d4.append("project_experience")
    d4 = min(d4, 20)

    # ---- D5 风险评估 ----
    d5 = 0
    missing_d5 = []
    country = buyer.get("country", "")
    sanctioned_country = is_sanctioned_country(country)
    sdn_hit = is_sanctioned_entity(buyer.get("importer_name", ""), snippet)
    has_dual_use = has_dual_use_term(text_blob)
    fraud_hits = has_fraud_term(text_blob)

    # Risk：未发现负面就给满分
    risk_count = (1 if sanctioned_country else 0) + (1 if sdn_hit else 0) + (1 if has_dual_use else 0)
    if fraud_hits or sanctioned_country or sdn_hit:
        # 任何制裁 / 欺诈 / SDN 命中 → 风险维度直接 0
        d5 = 0
    else:
        d5 = 15
    if sanctioned_country:
        missing_d5.append("country_sanctioned")
    if sdn_hit:
        missing_d5.append("sdn_match")
    if has_dual_use:
        missing_d5.append("dual_use_term_present")

    total = d1 + d2 + d3 + d4 + d5
    grade = "D"
    reason = ""
    for threshold, g, msg in GRADE_THRESHOLDS:
        if total >= threshold:
            grade, reason = g, msg
            break

    return {
        "D1_real": {"score": d1, "max": 25, "missing": missing_d1},
        "D2_size": {"score": d2, "max": 25, "missing": missing_d2},
        "D3_type": {"score": d3, "max": 15, "missing": missing_d3, "customer_type": ctype},
        "D4_procurement": {"score": d4, "max": 20, "missing": missing_d4},
        "D5_risk": {"score": d5, "max": 15, "missing": missing_d5},
        "total": total,
        "grade": grade,
        "grade_reason": reason,
    }


# ================================================================
# 7. 决策路由
# ================================================================

def recommend(grade: str, compliance_violations: List[str], fraud_terms: List[str]) -> Dict[str, str]:
    """根据 grade + 合规 violation + 欺诈信号给出 routing recommendation."""
    if compliance_violations:
        return {
            "action": "halt",
            "next_skill": "hlzd-trade-compliance (REQUIRED - sanctions / OFAC hit)",
            "priority": "P0",
            "rationale": "Compliance violation blocks outreach.",
        }
    if fraud_terms:
        return {
            "action": "halt",
            "next_skill": "hlzd-trade-compliance (review fraud signals)",
            "priority": "P0",
            "rationale": "Fraud risk signals present; manual review required.",
        }
    if grade == "A":
        return {
            "action": "outreach_24h",
            "next_skill": "hlzd-cold-outreach",
            "priority": "P1",
            "rationale": "Grade A: priority outreach within 24 hours.",
        }
    if grade == "B":
        return {
            "action": "outreach_48h",
            "next_skill": "hlzd-cold-outreach",
            "priority": "P2",
            "rationale": "Grade B: solid buyer, supplement missing fields then outreach.",
        }
    if grade == "C":
        return {
            "action": "nurture",
            "next_skill": "nurture-sequence (no Skill - manual email)",
            "priority": "P3",
            "rationale": "Grade C: nurture pool.",
        }
    return {
        "action": "archive",
        "next_skill": "(no action)",
        "priority": "P4",
        "rationale": "Grade D: archive.",
    }


# ================================================================
# 8. Pipeline main
# ================================================================

def evaluate_buyer(buyer: Dict[str, Any]) -> Dict[str, Any]:
    """评估单个 buyer：合规粗筛 → 评分 → 推荐。

    Compliance 优先委托给 hlzd-trade-compliance (W8).
    若 TC 不可用 (offline 等) 降级用本地静态 + fraud 启发式.
    """
    assert_buyer_shape(buyer)

    text_blob = " ".join(filter(None, [
        buyer.get("importer_name", ""),
        buyer.get("snippet", ""),
        buyer.get("country", ""),
    ]))

    # 1) Trade-Compliance Bridge (W8) — primary path
    tc_result = compliance_clearance_via_trade_compliance(
        buyer_name=buyer.get("importer_name", ""),
        buyer_country=buyer.get("country", ""),
        product=buyer.get("product", ""),
    )

    compliance_violations: List[str] = []
    compliance_source: str = ""
    if tc_result is not None:
        compliance_source = "hlzd-trade-compliance"
        for v in tc_result.get("violations", []):
            sev = v.get("severity", "REVIEW")
            rid = v.get("rule_id", "?")
            evi = v.get("evidence", "")
            sev_tag = "high" if sev == "BLOCK" else ("medium" if sev == "REVIEW" else "low")
            compliance_violations.append(f"{sev_tag}:{rid}:{evi}")
    else:
        # 2) Fallback: local inline static check
        compliance_source = "inline_fallback"
        if is_sanctioned_country(buyer.get("country", "")):
            compliance_violations.append(f"high:country_sanctioned:{buyer.get('country')}")
        if is_sanctioned_entity(buyer.get("importer_name", ""), buyer.get("snippet", "")):
            compliance_violations.append(f"high:sdn_match:{buyer.get('importer_name')}")
        if has_dual_use_term(text_blob):
            compliance_violations.append("medium:dual_use_term_detected")

    fraud_terms = has_fraud_term(text_blob)

    # Compliance passed = 没有 BLOCK 级别 violation
    compliance_blocked = any(v.startswith(("high:BLOCK", "high:country",
                                            "high:sdn_match"))
                              for v in compliance_violations) or tc_result is None and any(
                              v.startswith("high:") for v in compliance_violations)
    compliance_passed = not compliance_blocked and tc_result is not None
    if tc_result is None and not compliance_violations:
        compliance_passed = True  # fallback clean

    scoring = score_dimensional(buyer)
    rec = recommend(scoring["grade"], compliance_violations, fraud_terms)

    return {
        "importer_name": buyer.get("importer_name"),
        "country": buyer.get("country"),
        "company_score": scoring["total"],
        "company_grade": scoring["grade"],
        "scoring": scoring,
        "compliance": {
            "violations": compliance_violations,
            "passed": compliance_passed,
            "fraud_terms_detected": fraud_terms,
            "source": compliance_source,
            "final_action": (tc_result or {}).get("rationale", ""),
        },
        "recommendation": rec,
    }


def evaluate_many(buyers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """批量评估 + 分级汇总。"""
    results: List[Dict[str, Any]] = []
    errors: List[str] = []
    by_grade: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    halt_count = 0
    for b in buyers:
        try:
            r = evaluate_buyer(b)
            results.append(r)
            by_grade[r["company_grade"]] += 1
            if r["recommendation"]["action"] == "halt":
                halt_count += 1
        except DiligenceError as exc:
            errors.append(f"buyer={b.get('importer_name', '?')}: {exc}")

    return {
        "$schema": "hlzd/customer-due-diligence/v1",
        "evaluated": len(results),
        "failed": len(errors),
        "halt_recommended": halt_count,
        "by_grade": by_grade,
        "results": results,
        "errors": errors,
    }
