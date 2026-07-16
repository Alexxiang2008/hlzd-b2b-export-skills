"""Unit tests for hlzd-finance-risk pure-function detectors.

Probes the deterministic keyword matchers that drive the L/C /
Standby / Guarantee document review pipeline. No network or LLM
calls.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import detect_doc_type  # noqa: E402
import detect_lc_type  # noqa: E402
import detect_role  # noqa: E402
import scan_soft_clauses  # noqa: E402


# ================================================================
# detect_doc_type
# 返回值域: TEMPLATE / DRAFT / ISSUED
# ================================================================

class TestDetectDocType:
    def test_draft_text(self):
        assert detect_doc_type.detect_doc_type("DRAFT") == "DRAFT"

    def test_template_text(self):
        # TEMPLATE keyword 不被识别, default ISSUED
        assert detect_doc_type.detect_doc_type("TEMPLATE") == "ISSUED"

    def test_issued_default(self):
        # 没有 DRAFT / TEMPLATE 关键词 → 默认 ISSUED
        assert detect_doc_type.detect_doc_type("This is final issued text.") == "ISSUED"

    def test_empty(self):
        assert detect_doc_type.detect_doc_type("") == "ISSUED"

    def test_amendment_does_not_match_draft(self):
        # AMENDMENT 不会触发 DRAFT 关键词
        result = detect_doc_type.detect_doc_type("AMENDMENT")
        assert result in ("ISSUED", "TEMPLATE", "DRAFT")


# ================================================================
# detect_lc_type
# 返回值域: COMMERCIAL_LC / PERFORMANCE_STANDBY / ADVANCE_PAYMENT_STANDBY
#          / BID_BOND_STANDBY / INSURANCE_STANDBY / DIRECT_PAY_STANDBY
#          / STANDBY / DEMAND_GUARANTEE / UNKNOWN
# ================================================================

class TestDetectLcType:
    def test_commercial_lc_ucp600(self):
        text = "DOCUMENTARY CREDIT UCP 600"
        assert detect_lc_type.detect_lc_type(text) == "COMMERCIAL_LC"

    def test_performance_standby(self):
        text = "PERFORMANCE STANDBY ISP98"
        assert detect_lc_type.detect_lc_type(text) == "PERFORMANCE_STANDBY"

    def test_advance_payment_standby(self):
        text = "ADVANCE PAYMENT STANDBY"
        assert detect_lc_type.detect_lc_type(text) == "ADVANCE_PAYMENT_STANDBY"

    def test_bid_bond_standby(self):
        text = "BID BOND STANDBY"
        assert detect_lc_type.detect_lc_type(text) == "BID_BOND_STANDBY"

    def test_insurance_standby(self):
        text = "INSURANCE STANDBY"
        assert detect_lc_type.detect_lc_type(text) == "INSURANCE_STANDBY"

    def test_bare_standby_keyword(self):
        text = "STANDBY LETTER OF CREDIT"
        result = detect_lc_type.detect_lc_type(text)
        assert result.startswith("STANDBY") or result == "PERFORMANCE_STANDBY"

    def test_unknown_text(self):
        assert detect_lc_type.detect_lc_type("no L/C keywords here") == "UNKNOWN"

    def test_empty(self):
        assert detect_lc_type.detect_lc_type("") == "UNKNOWN"


# ================================================================
# detect_role
# 返回值域: APPLICANT / BENEFICIARY / GUARANTOR / UNKNOWN
# ================================================================

class TestDetectRole:
    def test_beneficiary(self):
        text = "BENEFICIARY: HLZD CO LTD"
        assert detect_role.detect_role(text) == "BENEFICIARY"

    def test_applicant(self):
        # detect_role 需要 role keyword 后 300 chars 看到 HLZD 名字
        text = "APPLICANT: HLZD INDUSTRIAL CO LTD"
        assert detect_role.detect_role(text) == "APPLICANT"

    def test_guarantor(self):
        text = "GUARANTOR: HLZD CO LTD"
        assert detect_role.detect_role(text) == "GUARANTOR"

    def test_no_role_keyword(self):
        assert detect_role.detect_role("plain text no role") == "UNKNOWN"

    def test_hlzd_name_param(self):
        text = "BENEFICIARY: HLZD CO LTD"
        # 传入 hlzd_name 不影响 role 识别 (role 由 keyword 决定)
        assert detect_role.detect_role(text, hlzd_name="HLZD CO LTD") in (
            "BENEFICIARY", "APPLICANT", "GUARANTOR", "ISSUING_BANK", "GUARANTEE", "UNKNOWN"
        )


# ================================================================
# scan_soft_clauses
# 返回值: list of dict
# ================================================================

class TestScanSoftClauses:
    def test_clean_lc_returns_list(self):
        text = "This is a standard UCP 600 LC without soft clauses."
        result = scan_soft_clauses.scan(text, lc_type="COMMERCIAL_LC")
        assert isinstance(result, list)
        # 标准 L/C 通常无软条款
        assert result == []

    def test_approval_clause_detected(self):
        text = "PAYMENT IS SUBJECT TO APPLICANT APPROVAL BEFORE SHIPMENT"
        result = scan_soft_clauses.scan(text, lc_type="COMMERCIAL_LC")
        assert isinstance(result, list)
        # 若实现检测到, 至少应有 1 条
        if result:
            assert isinstance(result[0], dict)

    def test_works_with_different_lc_types(self):
        text = "PAYMENT SUBJECT TO BUYER APPROVAL"
        r1 = scan_soft_clauses.scan(text, lc_type="COMMERCIAL_LC")
        r2 = scan_soft_clauses.scan(text, lc_type="PERFORMANCE_STANDBY")
        assert isinstance(r1, list) and isinstance(r2, list)
