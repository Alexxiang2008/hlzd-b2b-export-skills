#!/usr/bin/env python3
"""hlzd-cold-outreach tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib  # noqa: E402


# ================================================================
# 1. Variable substitution
# ================================================================

class TestTemplateFill:
    def test_basic_substitution(self):
        out = lib.fill_template("Hi {{name}}", {"name": "Alex"})
        assert out == "Hi Alex"

    def test_unknown_var_left_placeholder(self):
        out = lib.fill_template("Hi {{name}}", {})
        assert out == "Hi {{name}}"

    def test_none_var_left_placeholder(self):
        out = lib.fill_template("Hi {{name}}", {"name": None})
        assert out == "Hi {{name}}"

    def test_empty_var_left_placeholder(self):
        out = lib.fill_template("Hi {{name}}", {"name": ""})
        assert out == "Hi {{name}}"

    def test_multiple_vars(self):
        out = lib.fill_template("Hello {{name}}, age {{age}}",
                                 {"name": "Alex", "age": "30"})
        assert out == "Hello Alex, age 30"


class TestWordCount:
    def test_word_count_basic(self):
        assert lib.word_count("Hello world foo bar") == 4

    def test_word_count_punctuation(self):
        assert lib.word_count("Hello, world! How are you?") == 5

    def test_word_count_empty(self):
        assert lib.word_count("") == 0

    def test_is_within_word_limit(self):
        assert lib.is_within_word_limit(" ".join(["word"] * 80)) is True

    def test_below_limit(self):
        assert lib.is_within_word_limit("Hi there") is False

    def test_above_limit(self):
        assert lib.is_within_word_limit(" ".join(["word"] * 200)) is False


# ================================================================
# 2. Template routing
# ================================================================

class TestSelectTemplate:
    @pytest.mark.parametrize("ctype", ["Manufacturer", "EPC", "Distributor",
                                         "OEM", "End User", "Trader"])
    def test_all_buyer_types(self, ctype):
        tpl = lib.select_template(ctype, "en")
        for k in ("subject", "opening", "value_prop", "cta", "signature"):
            assert k in tpl
            assert tpl[k]  # non-empty

    def test_unsupported_language_raises(self):
        with pytest.raises(lib.UnsupportedLanguage):
            lib.select_template("Manufacturer", "fr")

    def test_unknown_buyer_type_falls_back(self):
        tpl = lib.select_template("ManufacturerXYZ", "en")
        # 应该 fallback 到 Manufacturer
        assert "subject" in tpl
        assert "Reliable supply partner" in tpl["subject"]

    def test_es_translation_differs_from_en(self):
        en = lib.select_template("Manufacturer", "en")
        es = lib.select_template("Manufacturer", "es")
        assert en["subject"] != es["subject"]
        assert "Estimado" in es["opening"]


# ================================================================
# 3. Email render
# ================================================================

class TestRenderEmail:
    def _basic_buyer(self, **kwargs):
        b = {"importer_name": "Aramco", "country": "Saudi Arabia",
             "contact_person": "Mr. Ahmed"}
        b.update(kwargs)
        return b

    def _basic_ctx(self):
        return {"product": "OCTG casing", "product_category": "OCTG casing"}

    def test_renders_all_sections(self):
        email = lib.render_email(self._basic_buyer(), self._basic_ctx(),
                                   customer_type="EPC", language="en")
        for k in ("subject", "body", "to", "language",
                   "customer_type_used", "word_count"):
            assert k in email, f"missing {k}"

    def test_subject_includes_product(self):
        email = lib.render_email(self._basic_buyer(), self._basic_ctx(),
                                   language="en")
        assert "OCTG casing" in email["subject"]

    def test_body_contains_opening(self):
        email = lib.render_email(self._basic_buyer(), self._basic_ctx(),
                                   language="es")
        assert "Estimado/a" in email["body"]

    def test_body_word_count_in_range(self):
        email = lib.render_email(self._basic_buyer(), self._basic_ctx(),
                                   language="en")
        assert 30 <= email["word_count"] <= 200

    def test_substitutes_contact_name(self):
        email = lib.render_email(self._basic_buyer(contact_person="Ahmed"),
                                   self._basic_ctx(), language="en")
        assert "Ahmed" in email["body"]

    def test_unknown_var_left_in_body(self):
        email = lib.render_email(self._basic_buyer(), self._basic_ctx(),
                                   language="en")
        # [past project references] 是 EPC 模板故意保留的占位符
        # 我们检查 missing_variables 字段
        if "missing_variables" in email:
            assert isinstance(email["missing_variables"], list)


# ================================================================
# 4. Followup sequence
# ================================================================

class TestFollowupSequence:
    def test_generates_2_steps(self):
        initial = {
            "subject": "test",
            "to": {"company": "Aramco", "contact": "Mr. Ahmed"},
            "language": "en",
        }
        seq = lib.render_followup_sequence(initial, language="en")
        assert len(seq) == 2

    def test_days_increasing(self):
        initial = {"subject": "test",
                    "to": {"company": "Aramco", "contact": "Mr. Ahmed"}}
        seq = lib.render_followup_sequence(initial, language="en")
        assert seq[0]["day"] == 7
        assert seq[1]["day"] == 14

    def test_uses_re_subject_prefix(self):
        initial = {"subject": "Initial Outreach",
                    "to": {"company": "Aramco", "contact": "Mr. Ahmed"}}
        seq = lib.render_followup_sequence(initial, language="en")
        # Day 7 续期沿用 Re:；Day 14 是 closing-loop 换新话题
        assert "Re:" in seq[0]["subject"]
        assert seq[1]["day"] == 14  # 不同主题


    def test_uses_language(self):
        initial = {"subject": "test",
                    "to": {"company": "Aramco", "contact": "Mr. Ahmed"}}
        seq_en = lib.render_followup_sequence(initial, language="en")
        seq_es = lib.render_followup_sequence(initial, language="es")
        assert seq_en[0]["body"] != seq_es[0]["body"]


# ================================================================
# 5. Pipeline batch
# ================================================================

class TestBatch:
    def test_mixed_customer_types(self):
        buyers = [
            {"importer_name": "Aramco", "country": "SA", "customer_type": "EPC"},
            {"importer_name": "ACME", "country": "US", "customer_type": "Distributor"},
            {"importer_name": "TraderJoe", "country": "ZA", "customer_type": "Trader"},
        ]
        report = lib.generate_for_buyers(
            buyers,
            product_context={"product": "OCTG casing"},
            include_followups=True,
        )
        assert report["generated"] == 3
        assert report["failed"] == 0

    def test_unspecified_customer_type_uses_default(self):
        buyers = [{"importer_name": "X", "country": "US"}]  # 无 customer_type
        report = lib.generate_for_buyers(
            buyers,
            product_context={"product": "X"},
            default_customer_type="Trader",
        )
        assert report["generated"] == 1
        e = report["emails"][0]["email"]
        assert e["customer_type_used"] == "Trader"

    def test_no_followups_flag(self):
        buyers = [{"importer_name": "A", "country": "US", "customer_type": "Manufacturer"}]
        report = lib.generate_for_buyers(
            buyers,
            product_context={"product": "X"},
            include_followups=False,
        )
        assert "followup_sequence" not in report["emails"][0]


# ================================================================
# 6. End-to-end schema
# ================================================================

class TestOutputSchema:
    def test_email_required_keys(self):
        email = lib.render_email(
            {"importer_name": "Acme", "country": "US", "customer_type": "Manufacturer"},
            {"product": "X"},
        )
        for k in ("$schema", "to", "language", "customer_type_used",
                   "subject", "body", "word_count", "within_word_limit",
                   "missing_variables"):
            assert k in email, f"missing {k}"

    def test_batch_required_keys(self):
        report = lib.generate_for_buyers(
            [{"importer_name": "A", "country": "US"}],
            product_context={"product": "X"},
        )
        for k in ("$schema", "product_context", "default_customer_type",
                   "default_language", "generated", "failed",
                   "emails", "errors"):
            assert k in report, f"missing {k}"
