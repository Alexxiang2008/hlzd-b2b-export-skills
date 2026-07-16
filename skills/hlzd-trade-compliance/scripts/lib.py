"""hlzd-trade-compliance shared library.

提供:
- 日志
- 错误归类
- 数据结构 (CheckResult / ComplianceReport)
- 制裁国家 master list (OFAC + EU + UN 综合性)
- 静态制裁名单 loader (OFAC SDN / EU / BIS / Denied Persons / Unverified)
- 公司名 / 国家 fuzzy match
- 4 道检查的统一接口 (sdn / eu / bis / embargo)
- Clearance 三态路由: CLEARED / PENDING_REVIEW / BLOCKED
- Audit trail schema (每道检查生成一条 timestamped entry)

设计: v0.1 静态 CSV / 字典, 真实生产接 OFAC SDN CSV API v0.2
"""
from __future__ import annotations

import csv
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-trade-compliance") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# 1. 错误归类
# ================================================================

class ComplianceError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-trade-compliance",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


class SourceDataMissing(ComplianceError):
    def __init__(self, source_name: str):
        super().__init__(f"source data missing: {source_name}",
                          source=source_name, recoverable=False)


class InvalidInputFormat(ComplianceError):
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


# ================================================================
# 2. 数据结构
# ================================================================

@dataclass
class CheckFlag:
    """单条检查命中记录."""
    rule_id: str             # e.g. "OFAC-SDN-name-match"
    severity: str            # "BLOCK" / "REVIEW" / "INFO"
    source: str              # "ofac_sdn" / "eu_consolidated" / "bis_entity" / "country_embargo"
    evidence: str            # e.g. "Wagner Group" (matched buyer name)
    rationale: str           # 单句解释
    recommended_action: str  # "HALT + escalate to compliance officer" 等

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    """单道检查结果."""
    check_name: str               # e.g. "ofac_sdn_name_match"
    source_version: str           # e.g. "static_2026_07"
    matched: bool
    flags: List[CheckFlag] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "source_version": self.source_version,
            "matched": self.matched,
            "flags": [f.to_dict() for f in self.flags],
            "metadata": self.metadata,
        }


@dataclass
class ComplianceReport:
    """完整合规报告."""
    schema_version: str = "hlzd/trade-compliance/v1"
    product: str = ""
    hs_code: str = ""
    buyer_name: str = ""
    buyer_country: str = ""
    end_use_country: str = ""
    incoterm: str = ""
    timestamp_utc: str = ""
    clearance: str = ""              # CLEARED / PENDING_REVIEW / BLOCKED
    final_action: str = ""          # "Proceed" / "Hold for review" / "Block + escalate"
    rationale: str = ""
    check_results: List[CheckResult] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    data_versions: Dict[str, str] = field(default_factory=dict)
    data_source_attribution: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "$schema": self.schema_version,
            "product": self.product,
            "hs_code": self.hs_code,
            "buyer_name": self.buyer_name,
            "buyer_country": self.buyer_country,
            "end_use_country": self.end_use_country,
            "incoterm": self.incoterm,
            "timestamp_utc": self.timestamp_utc,
            "clearance": self.clearance,
            "final_action": self.final_action,
            "rationale": self.rationale,
            "check_results": [cr.to_dict() for cr in self.check_results],
            "audit_trail": self.audit_trail,
            "data_versions": self.data_versions,
            "data_source_attribution": self.data_source_attribution,
        }


# ================================================================
# 3. 制裁国家 + 禁运项目综合
# ================================================================

# OFAC Country-Based 制裁列表（综合性 v0.1）
# 实际 v0.2 接 OFAC/EU/UN 实时 API
COUNTRY_EMBARGOES: Dict[str, Dict[str, Any]] = {
    "north korea": {"severity": "BLOCK", "rules": "OFAC 31 CFR 510; UN S/RES/1718"},
    "iran": {"severity": "BLOCK", "rules": "OFAC 31 CFR 560; EU 267/2012"},
    "syria": {"severity": "BLOCK", "rules": "OFAC 31 CFR 542; EU 36/2012"},
    "cuba": {"severity": "BLOCK", "rules": "OFAC 31 CFR 515"},
    "crimea": {"severity": "BLOCK", "rules": "OFAC 31 CFR 589"},
    "donetsk": {"severity": "BLOCK", "rules": "OFAC 31 CFR 590"},
    "luhansk": {"severity": "BLOCK", "rules": "OFAC 31 CFR 590"},
    "sevastopol": {"severity": "BLOCK", "rules": "OFAC 31 CFR 589"},
    "venezuela": {"severity": "REVIEW", "rules": "OFAC 31 CFR 591 (selective)"},
    "belarus": {"severity": "REVIEW", "rules": "OFAC 31 CFR 548 (selective)"},
    "russia": {"severity": "REVIEW", "rules": "OFAC 31 CFR 587 (selective)"},
    "myanmar": {"severity": "REVIEW", "rules": "OFAC 31 CFR 525 (selective)"},
    "zimbabwe": {"severity": "REVIEW", "rules": "OFAC 31 CFR 541"},
}

# 上述 dict 的 key 是 lower-cased country name

# 模糊匹配的 token 黑名单 — 避免 industrial / group / company 等泛词误命中
NAME_TOKEN_STOPWORDS: set = {
    "industrial", "commercial", "trading", "group", "limited", "company",
    "technology", "technologies", "engineering", "manufacturing",
    "international", "global", "world", "services", "industries",
}

# Country aliases（地区名称 → 国家）
COUNTRY_ALIASES: Dict[str, str] = {
    "dprk": "north korea", "nk": "north korea", "朝鲜": "north korea",
    "uae": "united arab emirates", "阿联酋": "united arab emirates",
    "kSA": "saudi arabia", "沙特": "saudi arabia",
    "Russia": "russia", "RF": "russia",
    "中国": "china", "CN": "china",
}


# ================================================================
# 4. ECCN / 双用途品类粗筛
# ================================================================

# v0.1: 关键字粗筛的双用途商品类目 (BIS Commerce Control List - simplified)
# 实时版本接 BIS CCL API
DUAL_USE_HS_KEYWORDS: Dict[str, Dict[str, Any]] = {
    # 加密类
    "encryption_module": {"eccn": "5A002", "severity": "REVIEW",
                            "rationale": "Encryption hardware likely controlled under Cat 5A002"},
    "quantum_cryptography": {"eccn": "5A002", "severity": "REVIEW",
                              "rationale": "Quantum cryptography under Cat 5A002"},
    # 高端材料
    "maraging_steel_350": {"eccn": "1C350", "severity": "REVIEW",
                              "rationale": "Maraging steel 350 controlled under Cat 1C350"},
    "high_strength_steel_1500": {"eccn": "1C350", "severity": "BLOCK",
                                    "rationale": "Steel >1500 MPa is dual-use"},
    "carbon_fiber_precursor": {"eccn": "1C350", "severity": "BLOCK",
                                  "rationale": "Carbon fiber precursor controlled"},
    # 化学品
    "chemical_weapon_precursor": {"eccn": "1C350", "severity": "BLOCK",
                                     "rationale": "CWC Schedule 1/2/3 precursor"},
    "biotoxin_agent": {"eccn": "1C351", "severity": "BLOCK",
                        "rationale": "Biological agents / toxins"},
    # 半导体
    "advanced_lithography_equipment": {"eccn": "3B002", "severity": "BLOCK",
                                            "rationale": "EUV lithography; FY2023 BIS expanded"},
    # UAV / 导弹
    "uav_airframe_above_300km": {"eccn": "9A012", "severity": "BLOCK",
                                    "rationale": "Long-endurance UAV"},
}


# OFAC / EU 常用双用途标记（轻量关键词版）
DUAL_USE_KEYWORDS: List[str] = [
    "dual-use", "dual use", "two-use", "two use",
    "encryption", "encryption module", "quantum cryptography",
    "maraging steel 350", "high-strength steel beyond 1500",
    "carbon fiber precursor", "chemical weapon precursor",
    "biotoxin", "bioweapon", "uav above 300km", "lithography",
    "OCTG for re-export", "maraging", "ballistic",
]


# ================================================================
# 5. Helper: company name / country name normalization
# ================================================================

def normalize_name(name: str) -> str:
    """通用公司名归一化: lowercase / strip / 去标点 / 去 suffixes."""
    if not name:
        return ""
    s = name.strip().lower()
    # 去标点
    s = re.sub(r"[,.\s]+", " ", s).strip()
    # 去常见 suffix
    for suf in ("co ltd", "co ltd.", "co., ltd.", "co.,ltd.", "co. ltd.",
                 "limited", "ltd.", "ltd", "llc", "inc.", "inc",
                 "corp.", "corp", "corporation", "gmbh",
                 "s.a.", "s.a", "s.l.", "company", "co.", "co"):
        s = re.sub(rf"\s+{re.escape(suf)}\s*$", "", s)
    return s[:80]


def normalize_country(country: str) -> str:
    """Country 归一化 + alias 解析."""
    if not country:
        return ""
    s = country.strip().lower()
    return COUNTRY_ALIASES.get(s, s)


def fuzzy_in(haystack: str, needle: str) -> bool:
    """大小写不敏感 substring match."""
    if not (haystack and needle):
        return False
    return needle.lower().strip() in haystack.lower()


# ================================================================
# 6. CSV / 静态列表 loader
# ================================================================

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_sanctions_csv(filename: str) -> List[Dict[str, str]]:
    """Read a sanctions CSV from data/ — returns list of dict rows.

    CSV 必须有 'name' 列.
    v0.1 容错: 文件不存在返回 [].
    """
    path = DEFAULT_DATA_DIR / filename
    if not path.exists():
        raise SourceDataMissing(filename)
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


# ================================================================
# 7. Audit trail helper
# ================================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_audit_entry(check: str, version: str, matched: bool,
                      flags_count: int) -> Dict[str, Any]:
    return {
        "check": check,
        "data_version": version,
        "matched": matched,
        "flags_count": flags_count,
        "timestamp_utc": now_iso(),
    }


# ================================================================
# 8. Schema validation
# ================================================================

def validate_input(transaction: Dict[str, Any]) -> None:
    """最低 input 完整性检查."""
    if not isinstance(transaction, dict):
        raise InvalidInputFormat("transaction must be a dict")
    if not transaction.get("buyer_name"):
        raise InvalidInputFormat("buyer_name required")
    if not transaction.get("buyer_country"):
        raise InvalidInputFormat("buyer_country required")
    # product / hs_code / end_use_country optional but recommended
