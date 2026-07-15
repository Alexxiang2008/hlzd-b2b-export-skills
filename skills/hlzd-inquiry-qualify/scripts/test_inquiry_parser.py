#!/usr/bin/env python3
"""HLZD Inquiry Parser — test suite.

覆盖：
- 5 维评分逻辑（高 / 中 / 低）
- 字段抽取（多语种、邮箱、电话、公司名）
- 合规粗筛（制裁国家、双重用途关键词）
- Red flag 识别（诈骗高危、紧迫感）
- 待确认问题生成（缺失维度反向映射）
- 端到端 schema 完整性

运行：
    pytest scripts/test_inquiry_parser.py -v
    pytest scripts/test_inquiry_parser.py --cov=inquiry_parser
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# 让脚本目录可被 import
sys.path.insert(0, str(Path(__file__).parent))
import inquiry_parser as ip  # noqa: E402


# ================================================================
# 1) 基础语言识别
# ================================================================

class TestLanguageDetection:
    def test_english_default(self):
        assert ip.detect_language("We need API 5CT casing for Saudi project") == "en"

    def test_chinese(self):
        assert ip.detect_language("我们需要石油套管，规格 API 5CT，5000 米") == "zh"

    def test_spanish(self):
        assert ip.detect_language("Necesitamos tubería de acero sin soldadura ASTM A106") == "es"

    def test_arabic(self):
        assert ip.detect_language("نحتاج إلى غلاف API 5CT لمنشأة النفط") == "ar"

    def test_russian(self):
        assert ip.detect_language("Нам нужны стальные трубы API 5L") == "ru"


# ================================================================
# 2) 字段抽取
# ================================================================

class TestFieldExtraction:
    def test_email_basic(self):
        text = "Contact me at ahmed.alrashid@aramco-trading.example.com today"
        assert ip.extract_email(text) == "ahmed.alrashid@aramco-trading.example.com"

    def test_email_none(self):
        assert ip.extract_email("Contact me by phone please") is None

    def test_phone_intl(self):
        text = "Phone: +966 13 872 1234"
        assert ip.extract_phone(text) and ip.extract_phone(text).startswith("+966")

    def test_phone_whatsapp(self):
        text = "WhatsApp: +966 50 123 4567"
        phone = ip.extract_phone(text)
        assert phone and ("966" in phone)

    def test_product_octg(self):
        text = "We need API 5CT L80 OCTG casing, 9 5/8 inch, BTC"
        p = ip.extract_product(text, "en")
        assert p["name"] == "OCTG"
        assert "L80" in p["specifications"] or any("L80" in s for s in p["specifications"])
        assert p["hs_code_suggestion"] == "730429"

    def test_quantity(self):
        text = "Quantity: 5000 meters, delivery in two batches"
        p = ip.extract_product(text, "en")
        assert p["quantity"] is not None
        assert "5000" in p["quantity"]

    def test_port_known(self):
        text = "Port: CIF Jeddah Islamic Port, Saudi Arabia"
        c = ip.extract_commercial(text)
        assert "Jeddah" in c["destination_port"]
        assert "Saudi" in c["destination_port"]

    def test_incoterm(self):
        text = "INCOTERMS: CIF Paita"  # 注意：连 INCOTERMS 都触发
        c = ip.extract_commercial(text)
        assert c["incoterm"] == "CIF"

    def test_target_price(self):
        text = "Target unit price: around USD 1450 per meter"
        c = ip.extract_commercial(text)
        assert c["target_price"] is not None
        assert "1450" in c["target_price"]

    def test_cert_api(self):
        text = "We require API 5CT and ISO 11960."
        t = ip.extract_technical(text, "Casing")
        assert "API 5CT" in t["certifications_required"]
        assert "ISO 11960" in t["certifications_required"]

    def test_application_oilfield(self):
        text = "For use in oilfield / downhole operations"
        t = ip.extract_technical(text, "Casing")
        assert t["application"] == "oilfield / downhole"

    def test_company_ltd(self):
        text = "Saudi Aramco Trading Co., 123 King Fahd Road"
        cust = ip.extract_customer(text)
        assert cust["company_name"] is not None
        assert "Aramco" in cust["company_name"] or "Trading" in cust["company_name"]

    def test_country_saudi(self):
        text = "We are based in Saudi Arabia"
        cust = ip.extract_customer(text)
        assert cust["country"] == "Saudi Arabia"

    def test_project_phase_tender(self):
        text = "We are in RFQ / tender stage for this project."
        ctx = ip.extract_project_context(text)
        assert ctx["project_phase"] == "tender"

    def test_tender_ref(self):
        text = "Tender ref: ARAMCO-TR-2026-Q3-OCTG-007"
        ctx = ip.extract_project_context(text)
        assert ctx["tender_ref"] is not None
        assert "ARAMCO-TR" in ctx["tender_ref"]


# ================================================================
# 3) 评分引擎
# ================================================================

class TestScoring:
    def test_high_quality_inquiry_grade_a_or_b(self):
        with open(Path(__file__).parent.parent / "assets/inquiry_samples/01-saudi-rfq.txt", encoding="utf-8") as f:
            text = f.read()
        result = ip.parse_inquiry(text)
        assert result["scoring"]["grade"] in ("A", "B"), f"expected A/B, got {result['scoring']['grade']} (total={result['scoring']['total']})"
        assert result["scoring"]["total"] >= 70

    def test_low_quality_inquiry_grade_d(self):
        with open(Path(__file__).parent.parent / "assets/inquiry_samples/02-noise-low-quality.txt", encoding="utf-8") as f:
            text = f.read()
        result = ip.parse_inquiry(text)
        assert result["scoring"]["grade"] == "D", f"expected D, got {result['scoring']['grade']} (total={result['scoring']['total']})"
        assert result["scoring"]["total"] < 50

    def test_short_input_forces_low_grade(self):
        result = ip.parse_inquiry("hi")
        assert result["scoring"]["grade"] == "D"

    def test_questions_target_missing_dims(self):
        with open(Path(__file__).parent.parent / "assets/inquiry_samples/02-noise-low-quality.txt", encoding="utf-8") as f:
            text = f.read()
        result = ip.parse_inquiry(text)
        # 噪音样本应该有很多问题
        assert len(result["questions_to_confirm"]) >= 3
        assert len(result["questions_to_confirm"]) <= 5  # 限额


# ================================================================
# 4) 合规粗筛
# ================================================================

class TestCompliance:
    def test_sanctioned_country_blocks(self):
        text = "Buyer in Iran, please quote"
        cust = {"country": "Iran"}
        c = ip.compliance_screening(text, cust, {})
        assert c["sanctioned_country_buyer"] is True
        assert c["passed"] is False

    def test_dual_use_triggers(self):
        text = "Need OCTG dual-use shipment for re-export"
        c = ip.compliance_screening(text, {"country": "UAE"}, {})
        assert c["two_use_items"] is True

    def test_clean_inquiry_passes(self):
        text = "Standard procurement from UAE"
        c = ip.compliance_screening(text, {"country": "UAE"}, {})
        assert c["passed"] is True
        assert c["sanctioned_country_buyer"] is False
        assert c["two_use_items"] is False


# ================================================================
# 5) Red flag 检测
# ================================================================

class TestRedFlags:
    def test_advance_payment_fraud(self):
        text = "100% advance payment to personal account OK"
        flags = ip.detect_red_flags(text)
        assert any("HIGH" in f for f in flags)

    def test_urgency_flag(self):
        text = "very urgent please reply asap"
        flags = ip.detect_red_flags(text)
        assert any("MEDIUM" in f for f in flags)

    def test_clean_input_no_flags(self):
        text = "We are a procurement officer at a state-owned oil company."
        flags = ip.detect_red_flags(text)
        assert flags == []


# ================================================================
# 6) 端到端 schema 完整性
# ================================================================

class TestEndToEnd:
    @pytest.fixture
    def saudi_result(self):
        with open(Path(__file__).parent.parent / "assets/inquiry_samples/01-saudi-rfq.txt", encoding="utf-8") as f:
            text = f.read()
        return ip.parse_inquiry(text)

    @pytest.fixture
    def peru_result(self):
        with open(Path(__file__).parent.parent / "assets/inquiry_samples/03-es-latam.txt", encoding="utf-8") as f:
            text = f.read()
        return ip.parse_inquiry(text)

    @pytest.fixture
    def fraud_result(self):
        with open(Path(__file__).parent.parent / "assets/inquiry_samples/04-fraud-ish.txt", encoding="utf-8") as f:
            text = f.read()
        return ip.parse_inquiry(text)

    def test_schema_keys_present(self, saudi_result):
        required_keys = {
            "$schema", "raw_text_hash", "detected_language",
            "extracted", "scoring", "questions_to_confirm",
            "red_flags", "compliance_check", "recommended_next_skill",
        }
        assert required_keys.issubset(saudi_result.keys())

    def test_schema_version(self, saudi_result):
        assert saudi_result["$schema"] == "hlzd/inquiry-qualify/v1"

    def test_extracted_subkeys(self, saudi_result):
        extracted = saudi_result["extracted"]
        assert {"product", "commercial", "technical", "customer", "project_context"}.issubset(extracted.keys())

    def test_scoring_breakdown(self, saudi_result):
        s = saudi_result["scoring"]
        assert {"D1_product", "D2_commercial", "D3_technical", "D4_customer", "D5_project"}.issubset(s.keys())
        assert "total" in s and "grade" in s

    def test_spanish_inquiry_recognized(self, peru_result):
        assert peru_result["detected_language"] == "es"
        assert peru_result["extracted"]["customer"]["country"] == "Peru"
        assert peru_result["extracted"]["technical"]["application"] is not None
        # 西班牙语 case 应该有合规过且 grade A/B（信息齐全）
        assert peru_result["scoring"]["grade"] in ("A", "B")

    def test_fraud_routes_to_compliance(self, fraud_result):
        assert any("HIGH" in f for f in fraud_result["red_flags"])
        assert "hlzd-trade-compliance" in fraud_result["recommended_next_skill"]

    def test_hash_deterministic(self):
        a = ip.hash_text("hello world")
        b = ip.hash_text("hello world")
        assert a == b
        assert a.startswith("sha256:")

    def test_json_serializable(self, saudi_result):
        # 必须能 round-trip JSON（重要：保证输出可被下游消费）
        s = json.dumps(saudi_result, ensure_ascii=False)
        restored = json.loads(s)
        assert restored["$schema"] == "hlzd/inquiry-qualify/v1"


# ================================================================
# 7) 工程品味
# ================================================================

class TestEngineering:
    def test_no_mutation_of_input(self):
        """parse_inquiry 不应该修改输入字符串。"""
        original = "We need API 5CT casing"
        ip.parse_inquiry(original)
        assert original == "We need API 5CT casing"

    def test_determinism(self):
        """相同输入必须产生相同输出（不含时间戳）。"""
        text = "Need 5000 meters API 5CT L80"
        r1 = ip.parse_inquiry(text)
        r2 = ip.parse_inquiry(text)
        # 移除 _meta.version 比较
        assert r1["scoring"] == r2["scoring"]
        assert r1["raw_text_hash"] == r2["raw_text_hash"]
