#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""不符点检测 — 基于 OCR 解析后的字段 dict"""
from typing import Any


def detect(parsed: dict) -> list:
    """基于 parsed 字段检测不符点。

    parsed 应包含字段：
        lc_type, expiry_date, latest_shipment_date, presentation_date,
        shipment_date, lc_amount, invoice_amount, insurance_amount,
        goods_amount, port_of_loading, port_of_discharge, lc_goods_description,
        invoice_goods_description, documents_required (list)
    """
    discrepancies = []
    lc_type = parsed.get("lc_type", "COMMERCIAL_LC")

    # === UCP 600 不符点（Commercial LC）===
    if lc_type == "COMMERCIAL_LC":
        # D-UCP-001: 过期
        if parsed.get("presentation_date") and parsed.get("expiry_date"):
            if parsed["presentation_date"] > parsed["expiry_date"]:
                discrepancies.append({"id": "D-UCP-001", "severity": "CRITICAL"})

        # D-UCP-002: 超出装期
        if parsed.get("shipment_date") and parsed.get("latest_shipment_date"):
            if parsed["shipment_date"] > parsed["latest_shipment_date"]:
                discrepancies.append({"id": "D-UCP-002", "severity": "CRITICAL"})

        # D-UCP-003: 交单期超 21 天
        if parsed.get("presentation_date") and parsed.get("shipment_date"):
            days = (parsed["presentation_date"] - parsed["shipment_date"]).days
            if days > parsed.get("presentation_period_days", 21):
                discrepancies.append({"id": "D-UCP-003", "severity": "HIGH"})

        # D-UCP-005: 保险金额不足
        if parsed.get("insurance_amount") and parsed.get("goods_amount"):
            if parsed["insurance_amount"] < parsed["goods_amount"] * 1.1:
                discrepancies.append({"id": "D-UCP-005", "severity": "HIGH"})

        # D-UCP-008: 港口不符
        if parsed.get("port_of_loading") and parsed.get("lc_port_of_loading"):
            if parsed["port_of_loading"] != parsed["lc_port_of_loading"]:
                discrepancies.append({"id": "D-UCP-008", "severity": "HIGH"})

        # D-UCP-009: 货物描述不符
        if parsed.get("invoice_goods_description") and parsed.get("lc_goods_description"):
            if parsed["invoice_goods_description"] != parsed["lc_goods_description"]:
                discrepancies.append({"id": "D-UCP-009", "severity": "HIGH"})

        # D-UCP-010: 金额超限
        if parsed.get("invoice_amount") and parsed.get("lc_amount"):
            if parsed["invoice_amount"] > parsed["lc_amount"] * 1.1:
                discrepancies.append({"id": "D-UCP-010", "severity": "HIGH"})

    # === ISP98 不符点（Standby LC）===
    elif lc_type in ("STANDBY", "PERFORMANCE_STANDBY", "ADVANCE_PAYMENT_STANDBY",
                     "BID_BOND_STANDBY", "DIRECT_PAY_STANDBY", "INSURANCE_STANDBY"):
        # D-ISP-001: 审单超 3 天（开证行侧）
        if parsed.get("review_time_banking_days", 0) > 3:
            discrepancies.append({"id": "D-ISP-001", "severity": "HIGH"})

        # D-ISP-002: 拒付通知超 4 天
        if parsed.get("refusal_notice_banking_days", 0) > 4:
            discrepancies.append({"id": "D-ISP-002", "severity": "HIGH"})

        # D-ISP-003: 备用 L/C 缺不可撤销声明
        if not parsed.get("is_irrevocable_explicit", False):
            discrepancies.append({"id": "D-ISP-003", "severity": "LOW"})

    # === URDG 758 不符点（Guarantee）===
    elif lc_type == "DEMAND_GUARANTEE":
        # D-URDG-001: 缺 supporting statement 要求
        if not parsed.get("supporting_statement_required", False):
            discrepancies.append({"id": "D-URDG-001", "severity": "HIGH"})

        # D-URDG-002: 保函付款超 7 天
        if parsed.get("payment_time_banking_days", 0) > 7:
            discrepancies.append({"id": "D-URDG-002", "severity": "HIGH"})

        # D-URDG-003: 反担保缺关键条款
        if parsed.get("is_counter_guarantee") and not all(
            parsed.get(k) for k in ("counter_guarantee_amount",
                                     "counter_guarantee_expiry",
                                     "counter_guarantee_governing_rules")
        ):
            discrepancies.append({"id": "D-URDG-003", "severity": "MEDIUM"})

    return discrepancies


if __name__ == "__main__":
    # 演示
    sample = {"lc_type": "COMMERCIAL_LC", "presentation_date": None}
    print(detect(sample))