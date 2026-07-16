"""HLZD B2B Skills Demo Orchestrator.

跑通 9 Skill 全链路：
  Step 1: hlzd-inquiry-qualify          (parse + 5-dim score)
  Step 2: hlzd-buyer-finder            (uses mock buyers since Volza is blocked)
  Step 3: hlzd-customer-due-diligence  (5-dim + compliance halt)
  Step 4: hlzd-cold-outreach            (email + Day 7/14)
  Step 5: hlzd-solution-match           (3 plans)
  Step 6: hlzd-quotation-gen            (FOB/CIF/DDP)
  Step 7: hlzd-negotiation-playbook     (3-round concession)

每个 scenario 一个 step-by-step JSON 落到 outputs/。

用法：
  py run_full_demo.py --scenario scenario-saudi-rfq
  py run_full_demo.py --scenario scenario-latam-solar
  py run_full_demo.py --scenario scenario-fraud-blocked
  py run_full_demo.py --all            # 跑全部 3 个
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent


def _load_lib(skill_name: str, alias: str,
              module_filename: str = "lib.py"):
    """Dynamically load a Skill's lib.py with a unique module name to avoid
    collision (多个 Skill 都用 'lib' as filename).
    """
    lib_path = ROOT / "skills" / skill_name / "scripts" / module_filename
    if not lib_path.exists():
        raise FileNotFoundError(f"missing lib: {lib_path}")
    spec = importlib.util.spec_from_file_location(alias, lib_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# 用 alias 区分不同 Skill 的 lib
# hlzd-inquiry-qualify 的核心模块名是 inquiry_parser.py（不是 lib.py）
iq_lib = _load_lib("hlzd-inquiry-qualify", "iq_lib", module_filename="inquiry_parser.py")
d_lib  = _load_lib("hlzd-customer-due-diligence", "diligence_lib")
o_lib  = _load_lib("hlzd-cold-outreach", "outreach_lib")
sm_lib = _load_lib("hlzd-solution-match", "solution_match_lib")
q_lib  = _load_lib("hlzd-quotation-gen", "quotation_lib")
n_lib  = _load_lib("hlzd-negotiation-playbook", "negotiation_lib")


SCENARIOS_DIR = Path(__file__).parent / "scenarios"
OUTPUTS_DIR = Path(__file__).parent / "outputs"


def step_1_inquiry_qualify(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Step 1: parse RFQ + 5-dim score."""
    text = scenario["inquiry"]["raw_text"]
    lang = scenario.get("language", "en")
    parsed = iq_lib.parse_inquiry(text)
    # parse_inquiry → 没评分逻辑；score_inquiry 才有
    # 注入语言
    parsed_detected_lang = parsed.get("detected_language")
    # 合成最终评估
    evaluation = iq_lib.evaluate_buyer({
        "importer_name": parsed.get("extracted", {}).get("customer", {}).get("company_name")
                            or "Unknown",
        "country": parsed.get("extracted", {}).get("customer", {}).get("country") or "?",
        "raw_text": text,
    }) if hasattr(iq_lib, "evaluate_buyer") else None
    return {
        "stage": "step_1_inquiry_qualify",
        "schema_version": "hlzd/inquiry-qualify/v1",
        "raw_text_hash": parsed.get("raw_text_hash"),
        "detected_language": parsed_detected_lang,
        "extracted": parsed.get("extracted"),
        "scoring": parsed.get("scoring"),
        "compliance_check": parsed.get("compliance_check"),
        "red_flags": parsed.get("red_flags"),
        "questions_to_confirm": parsed.get("questions_to_confirm"),
        "recommended_next_skill": parsed.get("recommended_next_skill"),
    }


def step_2_buyer_finder(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Step 2: 跳过网络 — 直接使用 scenario.mock_buyers。"""
    # 真实环境：调 buyer-finder.cli，但 Volza 免费版通常被屏蔽 → 落到 mock
    return {
        "stage": "step_2_buyer_finder",
        "schema_version": "hlzd/buyer-finder/v1",
        "method": "scenario_mock (Volza blocked in demo env)",
        "product": scenario["product_context"]["product"],
        "country": scenario.get("country_iso", "US"),
        "competitors": [],  # mock 模式下跳过去重真实竞对查找
        "importers": [
            {
                **b,
                "importer_name": b.get("importer_name"),
                "country": b.get("country"),
                "source": "scenario_mock_data",
            } for b in scenario.get("mock_buyers", [])
        ],
        "stats": {
            "competitors_found": 0,
            "importers_found_pre_dedup": len(scenario.get("mock_buyers", [])),
            "importers_after_dedup": len(scenario.get("mock_buyers", [])),
            "volza_quota_used": 0,
            "alibaba_quota_used": 0,
        },
        "warnings": ["running in demo mode - buyer-finder blocked, using scenario mock data"],
    }


def step_3_diligence(inquiry_report: Dict[str, Any],
                       buyers_report: Dict[str, Any]) -> Dict[str, Any]:
    """Step 3: 对每个 buyer 跑 5 维 + 合规。"""
    importers = buyers_report["importers"]
    if not importers:
        return {
            "stage": "step_3_customer_due_diligence",
            "schema_version": "hlzd/customer-due-diligence/v1",
            "evaluated": 0, "failed": 0, "halt_recommended": 0,
            "by_grade": {"A": 0, "B": 0, "C": 0, "D": 0},
            "results": [],
            "errors": [],
            "warnings": ["no importers to evaluate"],
        }
    return d_lib.evaluate_many(importers)


def step_4_outreach(diligence_report: Dict[str, Any],
                      scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Step 4: 给每个 A/B 等级 buyer 生成邮件草稿（含 Day 7/14 跟进）。"""
    if not diligence_report.get("results"):
        return {
            "stage": "step_4_cold_outreach",
            "schema_version": "hlzd/cold-outreach/v1-batch",
            "generated": 0, "failed": 0, "emails": [], "errors": [],
            "warnings": ["no buyers to outreach"],
        }
    if diligence_report.get("halt_recommended", 0) > 0:
        # 有 halt — 应当 skip 不发邮件（但仍展示 redirect）
        return {
            "stage": "step_4_cold_outreach",
            "schema_version": "hlzd/cold-outreach/v1-batch",
            "generated": 0, "failed": 0,
            "emails": [],
            "errors": [],
            "warnings": [f"HALT recommended for {diligence_report['halt_recommended']} buyers - "
                          "outreach skipped, routed to hlzd-trade-compliance instead"],
        }

    # 准备 buyer list：取 grade A + B
    a_b_buyers = [
        {"importer_name": r["importer_name"],
         "country": r["country"],
         "customer_type": r.get("scoring", {}).get("D3_type", {}).get("customer_type", "Manufacturer")}
        for r in diligence_report["results"]
        if r["company_grade"] in ("A", "B")
    ]
    if not a_b_buyers:
        return {
            "stage": "step_4_cold_outreach",
            "schema_version": "hlzd/cold-outreach/v1-batch",
            "generated": 0, "failed": 0, "emails": [], "errors": [],
            "warnings": ["no A/B-grade buyers to outreach"],
        }

    return o_lib.generate_for_buyers(
        a_b_buyers,
        product_context={
            "product": scenario["product_context"]["product"],
            "product_category": scenario["product_context"].get("product_category", "industrial equipment"),
            **scenario.get("sender_context", {}),
        },
        default_customer_type="Manufacturer",
        include_followups=True,
    )


def step_5_solution_match(scenario: Dict[str, Any],
                            language: str = "en") -> Dict[str, Any]:
    """Step 5: 3 套 SKU 方案匹配."""
    pc = scenario.get("product_context", {})
    if not pc.get("product"):
        return {
            "stage": "step_5_solution_match",
            "schema_version": "hlzd/solution-match/v1",
            "warning": "scenario missing product_context.product; skipping.",
        }
    quantity = scenario.get("enquiry_quantity", "500 tons")
    enquiry = {
        "product": pc["product"],
        "product_category": pc.get("product_category"),
        "quantity": quantity,
        "certifications_required": ["ISO 9001", "CE"],
        "text": scenario["inquiry"]["raw_text"][:500],
        "lead_time_days": scenario.get("redlines", {}).get("max_lead_time_days", 60),
    }
    return sm_lib.recommend_three(enquiry)


def step_6_quotation(solution_report: Dict[str, Any],
                       scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Step 6: 给 best_match 出 FOB/CIF/DDP 3 套报价."""
    best = solution_report.get("best_match", {})
    if not best or "specs" not in best:
        return {"stage": "step_6_quotation_gen",
                  "schema_version": "hlzd/quotation-gen/v1",
                  "warning": "no best_match from step 5; skipping quotation."}

    sku_meta = {
        "sku": best.get("sku"),
        "currency": "USD",
        "unit_price_per_ton": best["specs"].get("unit_price_per_ton", 1000),
    }
    quantity = float(scenario.get("enquiry_qty_num", 500.0))

    # 目标国家：从 scenario 顶层 country_iso 或第一个 buyer 推断
    target_country = scenario.get("country_iso", "")
    if not target_country and scenario.get("mock_buyers"):
        first = scenario["mock_buyers"][0]
        c = first.get("country", "")
        target_country = (c[:2] if c else "").upper() or "AE"
    if not target_country:
        target_country = "AE"

    return q_lib.calculate_quote(
        sku=sku_meta,
        quantity_tons=quantity,
        target_country=target_country,
        incoterm="FOB",
        target_currency="USD",
        profit_margin=0.18,
        containers=1,
    )


def step_7_negotiation(quotation_report: Dict[str, Any],
                         scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Step 7: 模拟客户出价 + 3 轮让步推演."""
    if not quotation_report.get("components"):
        return {"stage": "step_7_negotiation_playbook",
                  "schema_version": "hlzd/negotiation-playbook/v1",
                  "warning": "no quotation components from step 6; skipping."}
    initial_quote = {
        "quantity_tons": quotation_report.get("quantity_tons", 500),
        "incoterms": quotation_report.get("incoterms", {"FOB": {"total_usd": 0}}),
        "components": quotation_report["components"],
    }
    sku_meta_unit = quotation_report["components"].get("factory_unit_price_usd", 1000)
    target_price = round(sku_meta_unit * 0.88, 2)

    customer_response = {
        "target_price": target_price,
        "desired_lead_days": scenario.get("redlines", {}).get("max_lead_time_days", 30),
        "advance_pct": 30,
    }

    redlines = scenario.get("redlines", {})

    return n_lib.run_playbook(
        initial_quote=initial_quote,
        customer_response=customer_response,
        redlines=redlines or None,
        lose_to_competitor_risk=scenario.get("competitor_risk", False),
    )


def step_7_negotiation(quotation_report: Dict[str, Any],
                         scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Step 7: 模拟客户出价 + 3 轮让步推演."""
    initial_quote = {
        "quantity_tons": quotation_report["quantity_tons"],
        "incoterms": quotation_report["incoterms"],
        "components": quotation_report["components"],
    }
    # 客户报 target_price 设为 best_match.unit 的 88%
    sku_meta_unit = quotation_report["components"]["factory_unit_price_usd"]
    target_price = round(sku_meta_unit * 0.88, 2)

    customer_response = {
        "target_price": target_price,
        "desired_lead_days": scenario.get("redlines", {}).get("max_lead_time_days", 30),
        "advance_pct": 30,
    }

    redlines = scenario.get("redlines", {})

    return n_lib.run_playbook(
        initial_quote=initial_quote,
        customer_response=customer_response,
        redlines=redlines or None,
        lose_to_competitor_risk=scenario.get("competitor_risk", False),
    )


def run_scenario(scenario_path: Path) -> Dict[str, Any]:
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    print(f"\n{'=' * 72}\n  {scenario['scenario_id']}\n  {scenario['description']}\n{'=' * 72}")

    trace: Dict[str, Any] = {"scenario": scenario_path.stem,
                              "scenario_id": scenario["scenario_id"],
                              "stages": {}}

    # Step 1
    print("\n[1/7] inquiry-qualify ... ", end="")
    step1 = step_1_inquiry_qualify(scenario)
    grade = step1.get("scoring", {}).get("grade", "?")
    total = step1.get("scoring", {}).get("total", "?")
    print(f"grade={grade} total={total}")
    trace["stages"]["step_1"] = step1

    # Step 2
    print("[2/7] buyer-finder ... ", end="")
    step2 = step_2_buyer_finder(scenario)
    n_buyers = len(step2["importers"])
    print(f"{n_buyers} mock buyers loaded")
    trace["stages"]["step_2"] = step2

    # Step 3
    print("[3/7] customer-due-diligence ... ", end="")
    step3 = step_3_diligence(step1, step2)
    n_a_b = sum(1 for r in step3.get("results", []) if r.get("company_grade") in ("A", "B"))
    halt = step3.get("halt_recommended", 0)
    print(f"evaluated={step3['evaluated']} A/B={n_a_b} halt={halt}")
    trace["stages"]["step_3"] = step3

    # Step 4
    print("[4/7] cold-outreach ... ", end="")
    step4 = step_4_outreach(step3, scenario)
    print(f"generated={step4.get('generated', 0)}")
    trace["stages"]["step_4"] = step4

    # Step 5 (skip if halt)
    if halt > 0:
        print("[5/7] solution-match ... SKIPPED (halt)")
        step5 = {"stage": "step_5_solution_match",
                  "warning": "skipped - compliance halt in step_3",
                  "$schema": "hlzd/solution-match/v1"}
    else:
        print("[5/7] solution-match ... ", end="")
        try:
            step5 = step_5_solution_match(scenario)
            best_sku = step5.get("best_match", {}).get("sku", "?")
            print(f"best={best_sku}")
        except Exception as exc:
            print(f"ERROR: {exc}")
            step5 = {"stage": "step_5_solution_match", "error": str(exc)}
    trace["stages"]["step_5"] = step5

    # Step 6 (skip if halt)
    if halt > 0:
        print("[6/7] quotation-gen ... SKIPPED (halt)")
        step6 = {"stage": "step_6_quotation_gen",
                  "warning": "skipped - compliance halt in step_3",
                  "$schema": "hlzd/quotation-gen/v1"}
    else:
        print("[6/7] quotation-gen ... ", end="")
        try:
            step6 = step_6_quotation(step5, scenario)
            fob = step6.get("incoterms", {}).get("FOB", {}).get("total_usd", "?")
            margin = step6.get("profit_realized", {}).get("ratio")
            if isinstance(margin, float):
                print(f"FOB=${fob} margin={margin:.2%}")
            else:
                print(f"FOB=${fob}")
        except Exception as exc:
            print(f"ERROR: {exc}")
            step6 = {"stage": "step_6_quotation_gen", "error": str(exc)}
    trace["stages"]["step_6"] = step6

    # Step 7 (skip if halt or step 6 missing)
    if halt > 0 or not step6.get("incoterms"):
        print("[7/7] negotiation-playbook ... SKIPPED (halt)")
        step7 = {"stage": "step_7_negotiation_playbook",
                  "warning": "skipped - compliance halt or missing quotation",
                  "$schema": "hlzd/negotiation-playbook/v1"}
    else:
        print("[7/7] negotiation-playbook ... ", end="")
        try:
            step7 = step_7_negotiation(step6, scenario)
            decision = step7.get("decision", {}).get("decision", "?")
            print(f"decision={decision}")
        except Exception as exc:
            print(f"ERROR: {exc}")
            step7 = {"stage": "step_7_negotiation_playbook", "error": str(exc)}
    trace["stages"]["step_7"] = step7

    return trace


def main() -> int:
    parser = argparse.ArgumentParser(prog="hlzd-b2b-demo")
    parser.add_argument("--scenario", help="Path or id of scenario JSON (without .json)")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--output-dir", help="Output directory", default=str(OUTPUTS_DIR))
    args = parser.parse_args()

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.all:
        scenarios = sorted(SCENARIOS_DIR.glob("scenario-*.json"))
    elif args.scenario:
        sid = args.scenario
        sid = sid.removesuffix(".json") if sid.endswith(".json") else sid
        scenarios = [SCENARIOS_DIR / f"{sid}.json"]
    else:
        # 默认跑全部
        scenarios = sorted(SCENARIOS_DIR.glob("scenario-*.json"))

    if not scenarios:
        print("no scenarios found", file=sys.stderr)
        return 1

    for scenario_path in scenarios:
        if not scenario_path.exists():
            print(f"missing: {scenario_path}", file=sys.stderr)
            return 2
        trace = run_scenario(scenario_path)
        # 输出
        out_file = OUTPUTS_DIR / f"{scenario_path.stem}-trace.json"
        out_file.write_text(
            json.dumps(trace, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n   -> trace written: {out_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
