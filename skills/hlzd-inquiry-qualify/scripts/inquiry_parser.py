#!/usr/bin/env python3
"""HLZD Inquiry Parser - B2B industrial inquiry scoring engine.

零依赖核心：仅用 Python 标准库（re / json / hashlib）。
Pydantic v2 作为可选依赖（已安装则启用 schema 校验，未安装则 fallback 到 dict）。

Usage:
    python scripts/inquiry_parser.py --input path/to/inquiry.txt
    python scripts/inquiry_parser.py --input path/to/inquiry.txt --pretty
    python scripts/inquiry_parser.py --stdin < path/to/inquiry.txt
    echo "raw text" | python scripts/inquiry_parser.py --stdin --pretty

Output: JSON to stdout (CRM-ready). Exit 0 on success, 1 on error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ================================================================
# 0. Optional Pydantic v2 (best-effort schema validation)
# ================================================================

try:
    from pydantic import BaseModel, Field, ValidationError

    PYDANTIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYDANTIC_AVAILABLE = False

__version__ = "0.1.0"
SCHEMA_VERSION = "hlzd/inquiry-qualify/v1"


# ================================================================
# 1. 关键词字典（按语种） —— v0.1 覆盖 en / zh / es
#    二期扩展 ar / ru / pt
# ================================================================

PRODUCT_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "en": {
        "OCTG": ["OCTG", "oil country tubular"],
        "Casing": ["casing", "well casing", "casing pipe"],
        "Drill Pipe": ["drill pipe", "drillpipe"],
        "Steel Pipe": ["steel pipe", "seamless pipe", "welded pipe", "line pipe"],
        "Steel Structure": ["steel structure", "steel building", "prefab building", "pre-engineered"],
        "Container House": ["container house", "container home", "prefabricated house"],
        "Solar Panel": ["solar panel", "PV module", "photovoltaic"],
        "Cement": ["cement", "OPC cement", "Portland cement"],
        "Valve": ["ball valve", "gate valve", "check valve", "globe valve"],
        "Pump": ["centrifugal pump", "submersible pump", "diaphragm pump"],
        "Bearing": ["bearing", "ball bearing", "roller bearing"],
        "Fastener": ["bolt", "nut", "fastener", "anchor bolt"],
        "Cable": ["power cable", "control cable", "XLPE cable"],
        "Transformer": ["transformer", "power transformer", "distribution transformer"],
    },
    "zh": {
        "石油套管": ["石油套管", "套管", "无缝套管", "焊接套管"],
        "钢管": ["钢管", "无缝管", "焊接管"],
        "钢结构": ["钢结构", "钢构件", "装配式建筑"],
        "集装箱房屋": ["集装箱房屋", "集装箱房", "打包箱"],
        "太阳能板": ["太阳能板", "光伏组件"],
        "水泥": ["水泥", "普通硅酸盐水泥"],
        "阀门": ["阀门", "球阀", "闸阀"],
        "电缆": ["电缆", "电力电缆"],
        "变压器": ["变压器"],
    },
    "es": {
        "Tubería de acero": ["tubería de acero", "tubería sin soldadura", "tubería soldada"],
        "Estructura de acero": ["estructura de acero", "estructura metálica", "edificio prefabricado"],
        "Casa contenedor": ["casa contenedor", "contenedor habitable", "vivienda prefabricada"],
        "Panel solar": ["panel solar", "módulo fotovoltaico"],
        "Válvula": ["válvula", "válvula de bola", "válvula de compuerta"],
    },
}

CERT_KEYWORDS: Dict[str, List[str]] = {
    # API/ASME mechanical
    "API 5CT": ["API 5CT", "5CT"],
    "API 5L": ["API 5L", "5L PSL1", "5L PSL2"],
    "API 5DP": ["API 5DP", "5DP"],
    "ISO 11960": ["ISO 11960"],
    "ASME B16.9": ["ASME B16.9"],
    "ASME B31.3": ["ASME B31.3"],
    # Structural
    "ISO 9001": ["ISO 9001"],
    "ISO 14001": ["ISO 14001"],
    "EN 1090": ["EN 1090"],
    "AISC": ["AISC"],
    # Electrical / Solar
    "IEC 61215": ["IEC 61215"],
    "IEC 61730": ["IEC 61730"],
    "UL 1703": ["UL 1703"],
    # Safety / Environment
    "CE": [" CE ", " CE,", " CE.", "CE marking", "CE认证"],  # require word boundary
    "RoHS": ["RoHS", "RoHS 2.0"],
    "REACH": ["REACH"],
    "NACE MR0175": ["NACE MR0175", "MR0175"],
    # Material
    "ASTM A53": ["ASTM A53", "A53"],
    "ASTM A106": ["ASTM A106", "A106"],
    "EN 10210": ["EN 10210"],
    "EN 10219": ["EN 10219"],
}

INCOTERMS = ["EXW", "FOB", "CFR", "CIF", "CIP", "DAP", "DPU", "DDP"]
INCOTERMS_PATTERN = r"\b(" + "|".join(INCOTERMS) + r")\b"

UNITS_PATTERN = r"(?:meters?|m\b|metres?|ft|feet|tons?|MT|kg|lbs?|pieces?|pcs|units?|sets?|containers?|TEU|cartons?|pallets?)"

# 港口+国家组合（高频）
KNOWN_PORTS: Dict[str, str] = {
    # 沙特
    "jeddah": "Jeddah, Saudi Arabia",
    "dammam": "Dammam, Saudi Arabia",
    "yanbu": "Yanbu, Saudi Arabia",
    "riyadh": "Riyadh, Saudi Arabia",
    # 阿联酋
    "jebel ali": "Jebel Ali, UAE",
    "dubai": "Dubai, UAE",
    "abu dhabi": "Abu Dhabi, UAE",
    # 美国
    "houston": "Houston, TX, USA",
    "new orleans": "New Orleans, LA, USA",
    "long beach": "Long Beach, CA, USA",
    "new york": "New York, NY, USA",
    # 中国
    "shanghai": "Shanghai, China",
    "ningbo": "Ningbo, China",
    "shenzhen": "Shenzhen, China",
    "qingdao": "Qingdao, China",
    # 通用
    "rotterdam": "Rotterdam, Netherlands",
    "singapore": "Singapore",
    "lagos": "Lagos, Nigeria",
}

# 制裁国家（保守静态名单，需 hlzd-trade-compliance 二次复核）
SANCTIONED_COUNTRIES = {
    "north korea", "dprk", "iran", "syria", "cuba",
    "crimea", "donetsk", "luhansk", "sevastopol",
}

DUAL_USE_FLAG_TERMS = [
    "OCTG", "dual-use", "dual use", "two-use", "encryption",
    "cryptographic", "high-strength steel beyond 1500 MPa",
    "maraging steel 350",
]

# 欺诈 / 异常信号
RED_FLAG_HIGH = [
    "advance payment", "100% advance", "wire to personal",
    "western union", "money gram",
]
RED_FLAG_MEDIUM = [
    "urgent", "asap", "very urgent", "immediate shipment",
    "very serious buyer", "test order",
]


# ================================================================
# 2. 文本处理 / 语言检测
# ================================================================

def normalize(text: str) -> str:
    """轻量清洗：去除多余空白与控制字符。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_language(text: str) -> str:
    """轻量语种识别。优先显式线索，否则用 char-bucket 启发式。

    Returns: 语言代码 'en' / 'zh' / 'es' / 'ar' / 'ru' / 'pt' / 'other'
    """
    text_l = text.lower()
    # 显式信号（最快且 0 误判）
    if re.search(r"[一-鿿]", text):
        return "zh"
    if re.search(r"[؀-ۿ]", text):
        return "ar"
    if re.search(r"[Ѐ-ӿ]", text):
        return "ru"
    # 西班牙语特性字符
    if re.search(r"[ñáéíóúü]", text_l):
        return "es"
    # 葡语特性字符
    if re.search(r"[ãõç]", text_l):
        return "pt"
    # 默认英语
    return "en"


def hash_text(text: str) -> str:
    """用于去重 / 关联溯源。"""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ================================================================
# 3. 字段抽取
# ================================================================

def extract_email(text: str) -> Optional[str]:
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text: str) -> Optional[str]:
    # 国际格式 (含 + 国家码) 或本地格式
    patterns = [
        r"\+\d{1,4}[\s-]?\d{3,14}",  # +86 ...
        r"\+\d{1,4}[\s-]?\d{3,4}[\s-]?\d{3,4}[\s-]?\d{3,4}",
        r"\bWhatsApp[:\s+]*\+?\d[\d\s-]{8,}\b",
        r"\bTel[:\s+]*\+?\d[\d\s-]{8,}\b",
        r"\bPhone[:\s+]*\+?\d[\d\s-]{8,}\b",
        r"\bM[oO]b(?:ile)?[:\s+]*\+?\d[\d\s-]{8,}\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            cleaned = re.sub(r"[^\d+]", "", m.group(0))
            if 8 <= len(cleaned.replace("+", "")) <= 15:
                return cleaned
    return None


def extract_product(text: str, lang: str) -> Dict[str, Any]:
    """返回：name（最具体品类）/ specifications / quantity / hs_code_suggestion"""
    result: Dict[str, Any] = {
        "name": None,
        "specifications": [],
        "quantity": None,
        "hs_code_suggestion": None,
    }

    keyword_dict = PRODUCT_KEYWORDS.get(lang, PRODUCT_KEYWORDS["en"])

    # 1) 产品名：命中 keyword dict 中第一个出现的品类
    for cat, kws in keyword_dict.items():
        for kw in kws:
            if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                result["name"] = cat
                break
        if result["name"]:
            break

    # 2) 规格：API/ISO/ASTM/EN 标准号 + 尺寸/等级
    spec_patterns = [
        (r"\bAPI\s*\d+[A-Z]?\b", "API"),
        (r"\bISO\s*\d{4,5}\b", "ISO"),
        (r"\bASTM\s*[A-Z]?\s*\d{2,4}\b", "ASTM"),
        (r"\bEN\s*\d{3,5}\b", "EN"),
        (r"\bNACE\s*MR\s*\d{4}\b", "NACE"),
        (r"\b(A|B|C|D|L|N|P|Q|T)\s*80\b", "Material Grade"),  # material grades
        (r"\bJ55\b|\bK55\b|\bL80\b|\bN80\b|\bP110\b", "Material Grade"),
        (r"\b\d+\s?/\s?\d+\s*(?:inch|in|”)", "Size"),
        (r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m)\b", "Size"),
        (r"\b\d+\s*(?:MPa|psi|bar)\b", "Pressure"),
        (r"\b\d+\s*(?:V|kV|MV)\b", "Voltage"),
    ]
    specs = []
    for pat, label in spec_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            val = m.group(0).strip()
            specs.append(val)
            if len(specs) >= 12:
                break
        if len(specs) >= 12:
            break
    result["specifications"] = list(dict.fromkeys(specs))[:12]  # 去重保序

    # 3) 数量 — 贪婪匹配整段 "5000 meters"，避免被 \d{1,3} 截断
    qty_patterns = [
        # "5000 meters", "10,000 tons", "1,234,567.89 kg"
        r"\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{4,}(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
        r"(?:x\s*\d+\s*)?"
        + UNITS_PATTERN,
        # 带 "数量:" / "quantity:" / "qty:" 前缀
        r"(?:quantity|qty|amount|数量|cantidad)[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)\s*"
        + UNITS_PATTERN,
    ]
    for pat in qty_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["quantity"] = m.group(0).strip()
            break

    # 4) HS 编码建议（简单关键词 → 6 位映射）
    lc = text.lower()
    if any(k in lc for k in ["octg", "oil country tubular", "cas", "well casing"]):
        result["hs_code_suggestion"] = "730429"
    elif any(k in lc for k in ["container house", "prefabricated build", "container home"]):
        result["hs_code_suggestion"] = "9406"
    elif any(k in lc for k in ["steel structure", "steel building"]):
        result["hs_code_suggestion"] = "7308"
    elif any(k in lc for k in ["solar panel", "pv module"]):
        result["hs_code_suggestion"] = "8541"
    elif any(k in lc for k in ["cable", "wire harness"]):
        result["hs_code_suggestion"] = "8544"
    elif any(k in lc for k in ["transformer"]):
        result["hs_code_suggestion"] = "8504"
    elif any(k in lc for k in ["bearing"]):
        result["hs_code_suggestion"] = "8482"
    elif any(k in lc for k in ["fastener", "bolt"]):
        result["hs_code_suggestion"] = "7318"

    return result


def extract_commercial(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "destination_port": None,
        "incoterm": None,
        "target_price": None,
        "expected_delivery": None,
    }

    # 港口
    lc = text.lower()
    for port_key, port_label in KNOWN_PORTS.items():
        if port_key in lc:
            result["destination_port"] = port_label
            break
    if not result["destination_port"]:
        # fallback: "deliver to <City>" / "ship to <City>"
        m = re.search(r"(?:deliver|ship|to\s+)\s+to[:\s]+([A-Z][a-zA-Z\s,]+)", text)
        if m:
            result["destination_port"] = m.group(1).strip().rstrip(",.;")

    # INCOTERMS
    m = re.search(INCOTERMS_PATTERN, text)
    if m:
        result["incoterm"] = m.group(1).upper()

    # 目标价 / 预算
    price_patterns = [
        r"(?:target|target\s+price|target\s+unit\s+price|unit\s+price|price|预算|budget|目标价)[:\s\$€£]*([\d,]+(?:\.\d+)?)\s*(USD|EUR|RMB|CNY|GBP|\$|€|£)?\s*(?:/|per)?\s*(ton|tonne|meter|metre|m|piece|pc|pcs|unit|kg)?",
        r"(USD|EUR|RMB|CNY|\$|€|£)\s*([\d,]+(?:\.\d+)?)\s*(?:/|per)?\s*(ton|tonne|meter|metre|m|piece|pc|pcs|unit|kg)?",
        r"([\d,]+(?:\.\d+)?)\s*(USD|EUR|RMB|CNY|\$|€|£)\s*(?:/|per)?\s*(ton|tonne|meter|metre|m|piece|pc|pcs|unit|kg)?",
    ]
    for pat in price_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            # 提取整段价格表达
            full = m.group(0)
            # 清洗去前缀
            for prefix in ["target price:", "price:", "target unit price:", "budget:", "unit price:", "目标价:", "预算:"]:
                if full.lower().startswith(prefix.lower()):
                    full = full[len(prefix):].strip()
                    break
            result["target_price"] = full.strip()
            break

    # 期望交期
    delivery_patterns = [
        r"(?:delivery|by\s+delivery|ETA|deliver\s+by|expected\s+delivery|交期|交付)[:\s]+(\d{4}[-/]\d{1,2}|\d{4}\s*Q[1-4]|Q[1-4]\s*\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|within\s+\d+\s+(?:days|weeks|months))",
        r"(\d{4}[-/]\d{1,2})\s+(?:shipment|delivery)",
        r"(Q[1-4])\s*(\d{4})",
        r"(by\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
    ]
    for pat in delivery_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["expected_delivery"] = m.group(0).strip()
            break

    return result


def extract_technical(text: str, product_name: Optional[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "application": None,
        "certifications_required": [],
        "operating_conditions": {
            "pressure": None,
            "temperature": None,
            "media": None,
        },
    }

    # 应用场景
    app_keywords = {
        "oilfield / downhole": ["oilfield", "downhole", "down-hole", "well", "油气田", "井下"],
        "construction": ["construction", "building", "building project", "建筑", "施工"],
        "mining camp": ["mining camp", "mining site", "miner accommodation"],
        "hospital / healthcare": ["hospital", "healthcare", "clinic"],
        "solar farm / power plant": ["solar farm", "solar power", "photovoltaic power plant", "power station"],
        "hotel / hospitality": ["hotel", "resort", "hospitality"],
        "EPC / project": ["EPC", "turnkey", "engineering procurement"],
        "oil & gas pipeline": ["pipeline", "gas pipeline"],
        "water supply": ["water supply", "water treatment", "municipal water"],
        "refinery": ["refinery", "refinería", "refinación", "炼油", "石化", "petroquímicos", "petrochemical"],
        "power grid": ["power grid", "transmission line", "substation", "电网", "变电站"],
    }
    lc = text.lower()
    for app_label, keys in app_keywords.items():
        if any(k.lower() in lc for k in keys):
            result["application"] = app_label
            break

    # 认证
    certs = []
    for cert, pats in CERT_KEYWORDS.items():
        for pat in pats:
            # 用 regex 字面匹配（CE 用 lookahead/lookbehind 处理空格边界）
            safe_pat = pat if not pat.startswith(" ") and not pat.endswith(" ") else re.escape(pat)
            if re.search(safe_pat, text, re.IGNORECASE):
                if cert not in certs:
                    certs.append(cert)
                break
    result["certifications_required"] = certs

    # 工况
    p = re.search(r"(\d+(?:\.\d+)?)\s*(?:MPa|psi|bar)\b", text)
    if p:
        result["operating_conditions"]["pressure"] = p.group(0)

    t = re.search(r"(-?\d+)\s*(?:°?\s*C|°?\s*F|℃|℉|degC)\b", text)
    if t:
        result["operating_conditions"]["temperature"] = t.group(0)

    # 仅匹配 "media:" / "fluid:" 显式前缀；避免 "service" 模糊匹配
    m = re.search(r"\b(?:media|fluid)\s*:\s*([\w\s\-]{3,40})", text, re.IGNORECASE)
    if m:
        media_text = m.group(1).strip().rstrip(",.;")
        result["operating_conditions"]["media"] = media_text
    else:
        for kw in ["sour service", "sweet service", "H2S", "H₂S", "sea water", "seawater", "crude oil"]:
            if kw.lower() in lc:
                result["operating_conditions"]["media"] = kw
                break

    return result


def extract_customer(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "company_name": None,
        "contact_person": None,
        "title": None,
        "email": None,
        "phone": None,
        "linkedin": None,
        "country": None,
    }

    # Email
    email = extract_email(text)
    if email:
        result["email"] = email

    # Phone
    phone = extract_phone(text)
    if phone:
        result["phone"] = phone

    # LinkedIn
    m = re.search(r"(https?://)?(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9\-_/]+", text)
    if m:
        result["linkedin"] = m.group(0)
        if not m.group(1):
            result["linkedin"] = "https://" + result["linkedin"]

    # Contact person + title
    contact_patterns = [
        r"(?:Mr|Mrs|Ms|Dr|Eng)\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*[,\n]?\s*([\w\s]{2,40}?)(?:\n|Email|Tel|Phone|Mobile)",
        r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*[-,]\s*([\w\s]{2,40}?Manager|Engineer|Director|Buyer|Supervisor|President|CEO|CTO|Owner|Founder|Procurement|Sales|Operations)",
    ]
    for pat in contact_patterns:
        m = re.search(pat, text)
        if m:
            result["contact_person"] = m.group(1).strip()
            result["title"] = re.sub(r"\s+", " ", m.group(2).strip())[:40]
            break

    # Company name heuristic：含 Ltd / LLC / Inc. / Corp / Co., / GmbH / S.A. / 有限公司 / Co
    # 注意：[\w\s&.\-] 中 \s 仅匹配水平空白，禁止跨行匹配（否则会把签字人 + 职位误并入）。
    company_patterns = [
        # 优先级 1：独立 Co., / Co. / Company 后缀（不带 Ltd）
        r"([A-Z][\w &\.\-]{2,60}?[ \t]+(?:Co\.,|Co\.|Co,|Company))",
        # 优先级 2：完整法定后缀 (Co., Ltd. / LLC / Inc. / GmbH / S.A. 等)
        r"([A-Z][\w &\.\-]{2,60}?(?:Co\.,?[ \t]+Ltd\.?|Co\.?[ \t]+Ltd\.?|Limited|LLC|Inc\.?|Incorporated|Corp(?:oration)?|GmbH|S\.?A\.?|PLC|BV|Sdn\.?[ \t]+Bhd\.?|Pty\.?[ \t]+Ltd\.?))",
        # 优先级 3：西班牙/葡语 S.A.C / S.A. / S.L.
        r"([A-Z][\w &\.\-]{2,60}?(?:S\.?A\.?C\.?|S\.?L\.?))",
        # 中文
        r"([一-鿿]{2,30}(?:有限公司|股份有限公司|集团))",
        # Industry / Factory / Group 描述（同行一行）
        r"([A-Z][\w &\.\-]{2,40}[ \t]+(?:Industries|Industria|Manufacturing|Factory|Group|Company))",
    ]
    _COMPANY_BAD_STARTS = (
        # 句子 / 段落前缀
        "expansion ", "field ", "phase ", "we ", "acting ",
        "on behalf ", "for our ", "in saudi ", "pursuant to",
        "in accordance", "representing", "accordingly",
        "however", "therefore", "moreover",
        # 联系人 / 职位（不应被吃进 company）
        "mr.", "mr ", "mrs.", "mrs ", "ms.", "ms ", "dr.", "dr ",
        "eng.", "eng ", "ing.", "ing ",
        "gerente", "manager", "director", "buyer", "procurement", "sales ",
        "tel:", "email:", "phone:", "mobile:",
    )
    for pat in company_patterns:
        m = re.search(pat, text)
        if m:
            cand = m.group(1).strip().rstrip(",.;")
            cand_lc = cand.lower()
            if 4 <= len(cand) <= 120 and not any(cand_lc.startswith(b) for b in _COMPANY_BAD_STARTS):
                result["company_name"] = cand
                break

    # Country (大写/粗线索)
    country_keywords = {
        "Saudi Arabia": ["saudi", "kingdom of saudi", "KSA"],
        "United Arab Emirates": ["uae", "dubai", "abu dhabi", "emirates"],
        "United States": ["usa", " u.s.", "united states"],
        "Nigeria": ["nigeria"],
        "India": ["india"],
        "Brazil": ["brazil", "brasil"],
        "Mexico": ["mexico"],
        "Germany": ["germany", "deutschland"],
        "Spain": ["spain", "españa"],
        "Chile": ["chile"],
        "Peru": ["peru"],
        "Colombia": ["colombia"],
    }
    lc = text.lower()
    for country, kws in country_keywords.items():
        if any(k.lower() in lc for k in kws):
            result["country"] = country
            break

    return result


def extract_project_context(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "project_name": None,
        "project_phase": None,
        "epc_or_pmc": None,
        "tender_ref": None,
        "timeline": None,
    }

    lc = text.lower()

    # Phase
    if re.search(r"\b(tender|RFQ|RFP|tender invitation)\b", lc):
        result["project_phase"] = "tender"
    elif re.search(r"\b(LOI|letter of intent|意向)\b", lc):
        result["project_phase"] = "LOI"
    elif re.search(r"\b(PO|purchase order|订单)\b", lc):
        result["project_phase"] = "PO"
    elif re.search(r"\b(sourcing|looking for|seeking|quoted by)\b", lc):
        result["project_phase"] = "sourcing"

    # EPC / PMC
    epc_match = re.search(
        r"(on behalf of|representing|for|represent\s+)([\w\s\&\-\.]{2,60}?)(?:\s+(?:EPC|contractor|PMC|operator|end[- ]user))",
        text, re.IGNORECASE,
    )
    if epc_match:
        result["epc_or_pmc"] = epc_match.group(2).strip()

    # Tender ref
    tender_patterns = [
        r"(?:tender\s+(?:no|ref|reference|ID)|Ref[:\.\s]|招标号)[:\s]+([A-Z0-9\-/]{4,30})",
        r"\b(WB|World Bank|ADB|AfDB|IDB|IsDB|EBRD)\s+(?:project\s+)?([A-Z0-9\-/]{4,30})",
    ]
    for pat in tender_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["tender_ref"] = m.group(0).strip()
            break

    # Project name
    proj_match = re.search(r"(?:project|projects)\s+(?:name)?\s*[:\-]?\s*([A-Z][\w\s\-]{3,50}?)(?:\.|,|\n|$)", text)
    if proj_match:
        cand = proj_match.group(1).strip()
        if 3 <= len(cand) <= 60 and cand.split()[0].lower() not in ("is", "for", "in"):
            result["project_name"] = cand

    # Timeline
    timeline_match = re.search(r"(?:timeline|delivery\s+schedule|schedule|时间表)[:\s]+([\w\s\-\/,]{3,80})", text, re.IGNORECASE)
    if timeline_match:
        result["timeline"] = timeline_match.group(1).strip()[:80]

    return result


# ================================================================
# 4. 5 维评分引擎
# ================================================================

def score_inquiry(
    product: Dict[str, Any],
    commercial: Dict[str, Any],
    technical: Dict[str, Any],
    customer: Dict[str, Any],
    project_ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """依据 references/scoring-rubric.md 计算 5 维 + 总分 + Grade。"""

    # D1 产品（25）
    d1 = 0
    missing_d1 = []
    if product.get("name"):
        d1 += 8
    else:
        missing_d1.append("product_name")
    if product.get("specifications"):
        d1 += min(10, 2 * len(product["specifications"]))
    else:
        missing_d1.append("specifications")
    if product.get("quantity"):
        d1 += 7
    else:
        missing_d1.append("quantity")
    d1 = min(d1, 25)

    # D2 商务（25）
    d2 = 0
    missing_d2 = []
    if commercial.get("destination_port"):
        d2 += 6
    else:
        missing_d2.append("destination_port")
    if commercial.get("incoterm"):
        d2 += 6
    else:
        missing_d2.append("incoterm")
    if commercial.get("target_price"):
        d2 += 8
    else:
        missing_d2.append("target_price")
    if commercial.get("expected_delivery"):
        d2 += 5
    else:
        missing_d2.append("expected_delivery")
    d2 = min(d2, 25)

    # D3 技术（25）
    d3 = 0
    missing_d3 = []
    if technical.get("application"):
        d3 += 7
    else:
        missing_d3.append("application")
    certs = technical.get("certifications_required") or []
    if certs:
        d3 += min(10, 3 + 2 * (len(certs) - 1))
    else:
        missing_d3.append("certifications_required")
    oc = technical.get("operating_conditions") or {}
    ops_filled = sum(1 for v in [oc.get("pressure"), oc.get("temperature"), oc.get("media")] if v)
    if ops_filled >= 2:
        d3 += 8
    elif ops_filled == 1:
        d3 += 4
    else:
        missing_d3.append("operating_conditions (pressure/temperature/media)")
    d3 = min(d3, 25)

    # D4 客户（15）
    d4 = 0
    missing_d4 = []
    if customer.get("company_name"):
        d4 += 4
    else:
        missing_d4.append("company_name")
    if customer.get("contact_person"):
        d4 += 2
    else:
        missing_d4.append("contact_person")
    if customer.get("title"):
        d4 += 2
    else:
        missing_d4.append("title")
    email = customer.get("email") or ""
    if email:
        free_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "qq.com", "163.com", "126.com"}
        domain = email.split("@")[-1].lower() if "@" in email else ""
        d4 += 1 if domain in free_domains else 3
    else:
        missing_d4.append("email")
    if customer.get("phone"):
        d4 += 2
    else:
        missing_d4.append("phone")
    if customer.get("linkedin"):
        d4 += 2
    else:
        missing_d4.append("linkedin")
    d4 = min(d4, 15)

    # D5 项目（10）
    d5 = 0
    missing_d5 = []
    if project_ctx.get("project_name") or project_ctx.get("project_phase"):
        d5 += 4
    else:
        missing_d5.append("project_name_or_phase")
    if project_ctx.get("epc_or_pmc"):
        d5 += 2
    else:
        missing_d5.append("epc_or_pmc")
    if project_ctx.get("tender_ref"):
        d5 += 2
    else:
        missing_d5.append("tender_ref")
    if project_ctx.get("timeline"):
        d5 += 2
    else:
        missing_d5.append("timeline")
    d5 = min(d5, 10)

    total = d1 + d2 + d3 + d4 + d5

    if total >= 90:
        grade, reason = "A", "Strong inquiry across all dimensions. Assign senior sales within 24h."
    elif total >= 70:
        grade, reason = "B", "Solid inquiry with manageable gaps. Assign sales within 48h and request missing fields."
    elif total >= 50:
        grade, reason = "C", "Marginal inquiry - move to nurture pool, re-evaluate in 90 days."
    else:
        grade, reason = "D", "Low quality or non-actionable - auto-template reply and archive."

    return {
        "D1_product": {"score": d1, "max": 25, "missing": missing_d1},
        "D2_commercial": {"score": d2, "max": 25, "missing": missing_d2},
        "D3_technical": {"score": d3, "max": 25, "missing": missing_d3},
        "D4_customer": {"score": d4, "max": 15, "missing": missing_d4},
        "D5_project": {"score": d5, "max": 10, "missing": missing_d5},
        "total": total,
        "grade": grade,
        "grade_reason": reason,
    }


# ================================================================
# 5. 待确认问题生成
# ================================================================

QUESTION_TEMPLATES: Dict[str, str] = {
    # D1
    "product_name":       "Could you specify the exact product category you require (with model/series if any)?",
    "specifications":     "Could you share detailed technical specifications (size / grade / standard)?",
    "quantity":           "What is the expected order quantity and unit?",
    # D2
    "destination_port":   "Could you confirm the final destination port (city + country)?",
    "incoterm":           "Which INCOTERMS 2020 term should we quote against (FOB / CIF / DDP etc.)?",
    "target_price":       "Could you share your target unit price or budget range (with currency)?",
    "expected_delivery":  "What is your required delivery date / time window?",
    # D3
    "application":        "What is the end-use application scenario for this product?",
    "certifications_required": "Which quality/certification standards are mandatory (API / ISO / CE / RoHS)?",
    "operating_conditions (pressure/temperature/media)":
        "Could you share the operating pressure, temperature and service media (especially H2S if any)?",
    # D4
    "company_name":       "What is the full legal entity name of your company?",
    "contact_person":     "Who is the primary point of contact (name + title)?",
    "title":              "Could you provide the contact's job title?",
    "email":              "Could you share a business email (not personal mailbox) for follow up?",
    "phone":              "What is the best phone/WhatsApp number for urgent coordination?",
    "linkedin":           "Do you have a LinkedIn profile we may add to verify identity?",
    # D5
    "project_name_or_phase": "Which project / phase is this inquiry tied to (name, tender, or EPC)?",
    "epc_or_pmc":         "Are you the end user, an EPC contractor, or acting on behalf of another party?",
    "tender_ref":         "Is there a tender reference / project ID we should quote against?",
    "timeline":           "Could you share the project delivery timeline / key milestones?",
}


def build_questions(scoring: Dict[str, Any]) -> List[str]:
    questions: List[str] = []
    for dim in ["D1_product", "D2_commercial", "D3_technical", "D4_customer", "D5_project"]:
        block = scoring.get(dim, {})
        for k in block.get("missing", []):
            q = QUESTION_TEMPLATES.get(k)
            if q:
                questions.append(q)
    # 优先级：先 D3 (技术) 再 D2 (商务) 再其他
    # 但简单做：按原始顺序，前 5
    seen = set()
    ordered = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            ordered.append(q)
    return ordered[:5]


# ================================================================
# 6. 合规粗筛
# ================================================================

def compliance_screening(
    text: str, customer: Dict[str, Any], product: Dict[str, Any]
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "two_use_items": False,
        "sanctioned_country_buyer": False,
        "sanctioned_entity_buyer": False,
        "passed": True,
        "notes": [],
    }

    lc = text.lower()

    # Dual-use 关键词
    for term in DUAL_USE_FLAG_TERMS:
        if term.lower() in lc:
            result["two_use_items"] = True
            result["notes"].append(f"dual-use term detected: {term}")
            break

    # 制裁国家
    country = (customer.get("country") or "").lower()
    if any(sc in country for sc in SANCTIONED_COUNTRIES):
        result["sanctioned_country_buyer"] = True
        result["notes"].append(f"buyer country in sanctioned list: {customer.get('country')}")

    # 制裁实体（粗筛：含关键政治人物姓氏 — 留接口，二期接 OFAC SDN API）
    sanctioned_pattern = [
        r"\b(Kim Jong|Nikolas Maduro|Hezbollah|Hamas|Wagner|Russian\s+PMC|Islamic\s+State)\b",
    ]
    for pat in sanctioned_pattern:
        if re.search(pat, text, re.IGNORECASE):
            result["sanctioned_entity_buyer"] = True
            result["notes"].append(f"sanctioned-entity pattern hit: {pat}")
            break

    # 终判
    if result["sanctioned_country_buyer"] or result["sanctioned_entity_buyer"]:
        result["passed"] = False

    return result


# ================================================================
# 7. Red flags
# ================================================================

def detect_red_flags(text: str) -> List[str]:
    lc = text.lower()
    flags = []
    for kw in RED_FLAG_HIGH:
        if kw.lower() in lc:
            flags.append(f"HIGH: '{kw}' suggests potential fraud - escalate to compliance.")
    for kw in RED_FLAG_MEDIUM:
        if kw.lower() in lc:
            flags.append(f"MEDIUM: '{kw}' is overused in low-quality/spam RFQs.")
    return flags


# ================================================================
# 8. 推荐下一步 Skill
# ================================================================

def recommend_next(grade: str, compliance_passed: bool, red_flags: List[str]) -> str:
    if not compliance_passed:
        return "hlzd-trade-compliance (REQUIRED - sanctions triggered)"
    if any("HIGH" in f for f in red_flags):
        return "hlzd-trade-compliance (HIGH risk red flag detected)"
    if grade in ("A", "B"):
        return "hlzd-customer-due-diligence"
    if grade == "C":
        return "nurture-sequence (no Skill yet - use marketing-ideas/manual template)"
    return "archive-only (no Skill - auto template reply)"


# ================================================================
# 9. 主流程
# ================================================================

def parse_inquiry(raw_text: str) -> Dict[str, Any]:
    text = normalize(raw_text)
    if len(text) < 20:
        return {
            "$schema": SCHEMA_VERSION,
            "raw_text_hash": hash_text(text),
            "detected_language": detect_language(text),
            "extracted": {
                "product": {}, "commercial": {}, "technical": {},
                "customer": {}, "project_context": {},
            },
            "scoring": {
                "D1_product": {"score": 0, "max": 25, "missing": ["input too short"]},
                "D2_commercial": {"score": 0, "max": 25, "missing": ["input too short"]},
                "D3_technical": {"score": 0, "max": 25, "missing": ["input too short"]},
                "D4_customer": {"score": 0, "max": 15, "missing": ["input too short"]},
                "D5_project": {"score": 0, "max": 10, "missing": ["input too short"]},
                "total": 0,
                "grade": "D",
                "grade_reason": "Inquiry text too short (<20 chars) for meaningful assessment.",
            },
            "questions_to_confirm": [
                "Could you provide the full inquiry text?",
            ],
            "red_flags": [],
            "compliance_check": {
                "two_use_items": False,
                "sanctioned_country_buyer": False,
                "sanctioned_entity_buyer": False,
                "passed": True,
                "notes": ["input too short for compliance scan"],
            },
            "recommended_next_skill": "nurture-sequence",
            "_meta": {"version": __version__, "engine": "inquiry_parser"},
        }

    lang = detect_language(text)

    product = extract_product(text, lang)
    commercial = extract_commercial(text)
    technical = extract_technical(text, product.get("name"))
    customer = extract_customer(text)
    project_ctx = extract_project_context(text)

    scoring = score_inquiry(product, commercial, technical, customer, project_ctx)
    questions = build_questions(scoring)
    compliance = compliance_screening(text, customer, product)
    red_flags = detect_red_flags(text)
    next_skill = recommend_next(scoring["grade"], compliance["passed"], red_flags)

    result: Dict[str, Any] = {
        "$schema": SCHEMA_VERSION,
        "raw_text_hash": hash_text(text),
        "detected_language": lang,
        "extracted": {
            "product": product,
            "commercial": commercial,
            "technical": technical,
            "customer": customer,
            "project_context": project_ctx,
        },
        "scoring": scoring,
        "questions_to_confirm": questions,
        "red_flags": red_flags,
        "compliance_check": compliance,
        "recommended_next_skill": next_skill,
        "_meta": {"version": __version__, "engine": "inquiry_parser"},
    }
    return result


# ================================================================
# 10. CLI 入口
# ================================================================

def cli() -> int:
    parser = argparse.ArgumentParser(
        prog="hlzd-inquiry-parser",
        description="Parse B2B industrial inquiries and output 5-dim scored JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python scripts/inquiry_parser.py --input sample.txt --pretty\n"
            "  cat sample.txt | python scripts/inquiry_parser.py --stdin\n"
        ),
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--input", "-i", help="Path to inquiry file (txt or md)")
    grp.add_argument("--stdin", "-s", action="store_true", help="Read inquiry from stdin")

    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    try:
        if args.stdin:
            raw = sys.stdin.read()
        else:
            raw = Path(args.input).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        try:
            raw = Path(args.input).read_text(encoding="gbk")
        except Exception as exc:
            print(f"error: cannot decode file: {exc}", file=sys.stderr)
            return 1

    if not raw.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    try:
        result = parse_inquiry(raw)
    except Exception as exc:
        print(f"error: parsing failed: {exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
