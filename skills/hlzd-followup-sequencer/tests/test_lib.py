"""Unit tests for hlzd-followup-sequencer."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lib  # noqa: E402


# ================================================================
# parse_iso_date
# ================================================================

class TestParseIsoDate:
    def test_iso_with_z(self):
        dt = lib.parse_iso_date("2026-07-01T10:00:00Z")
        assert dt.year == 2026
        assert dt.month == 7
        assert dt.day == 1
        assert dt.tzinfo is not None

    def test_iso_date_only(self):
        dt = lib.parse_iso_date("2026-07-01")
        assert dt == datetime(2026, 7, 1, tzinfo=timezone.utc)

    def test_iso_with_timezone_offset(self):
        dt = lib.parse_iso_date("2026-07-01T10:00:00+00:00")
        assert dt.tzinfo is not None

    def test_iso_with_space(self):
        dt = lib.parse_iso_date("2026-07-01 10:00:00")
        assert dt.year == 2026

    def test_empty_raises(self):
        with pytest.raises(lib.InvalidEmailRecord):
            lib.parse_iso_date("")

    def test_bad_format_raises(self):
        with pytest.raises(lib.InvalidEmailRecord):
            lib.parse_iso_date("not-a-date")


# ================================================================
# days_since
# ================================================================

class TestDaysSince:
    def test_positive_days(self):
        sent = datetime(2026, 7, 1, tzinfo=timezone.utc)
        now = datetime(2026, 7, 9, tzinfo=timezone.utc)
        assert lib.days_since(sent, now=now) == 8

    def test_zero_days(self):
        now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
        assert lib.days_since(now, now=now) == 0

    def test_negative_days_future(self):
        sent = datetime(2026, 7, 10, tzinfo=timezone.utc)
        now = datetime(2026, 7, 1, tzinfo=timezone.utc)
        assert lib.days_since(sent, now=now) < 0


# ================================================================
# stage_for_days
# ================================================================

class TestStageForDays:
    def test_pending_below_7(self):
        assert lib.stage_for_days(0) == "pending"
        assert lib.stage_for_days(3) == "pending"
        assert lib.stage_for_days(6) == "pending"

    def test_day_7_nudge(self):
        assert lib.stage_for_days(7) == "day_7_nudge"
        assert lib.stage_for_days(10) == "day_7_nudge"
        assert lib.stage_for_days(13) == "day_7_nudge"

    def test_day_14_followup(self):
        assert lib.stage_for_days(14) == "day_14_followup"
        assert lib.stage_for_days(17) == "day_14_followup"
        assert lib.stage_for_days(20) == "day_14_followup"

    def test_day_21_breakup(self):
        assert lib.stage_for_days(21) == "day_21_breakup"
        assert lib.stage_for_days(30) == "day_21_breakup"

    def test_negative_days_returns_pending(self):
        assert lib.stage_for_days(-1) == "pending"


# ================================================================
# pick_template
# ================================================================

class TestPickTemplate:
    def test_english(self):
        tpl = lib.pick_template("day_7_nudge", "en")
        assert tpl is not None
        assert "subject_prefix" in tpl
        assert "body" in tpl

    def test_spanish(self):
        tpl = lib.pick_template("day_7_nudge", "es")
        assert tpl is not None
        assert "Estimado" in tpl["body"]

    def test_unknown_lang_falls_back_to_english(self):
        tpl = lib.pick_template("day_7_nudge", "de")
        assert tpl is not None
        # English fallback
        assert "Hi " in tpl["body"]

    def test_unknown_stage_returns_none(self):
        assert lib.pick_template("day_99_unknown", "en") is None


# ================================================================
# fill_placeholders
# ================================================================

class TestFillPlaceholders:
    def test_basic(self):
        out = lib.fill_placeholders("Hi {name}", {"name": "Alex"})
        assert out == "Hi Alex"

    def test_missing_keeps_placeholder(self):
        out = lib.fill_placeholders("Hi {name}, age {age}", {"name": "Alex"})
        # age missing -> leave as {{age}}
        assert "Hi Alex" in out
        assert "{age}" in out

    def test_none_keeps_placeholder(self):
        out = lib.fill_placeholders("{x}", {"x": None})
        assert out == "{x}"


# ================================================================
# process_email
# ================================================================

class TestProcessEmail:
    def _email(self, sent_at: str) -> dict:
        return {
            "to": {"company": "Aramco", "contact": "Mr. Ahmed", "country": "SA"},
            "subject": "OCTG casing for Saudi",
            "body": "Hi Mr. Ahmed, ...",
            "language": "en",
            "product_category": "OCTG casing",
            "sent_at": sent_at,
        }

    def test_pending_when_too_early(self):
        email = self._email("2026-07-15T10:00:00Z")
        now = datetime(2026, 7, 17, tzinfo=timezone.utc)  # 2 days after
        result = lib.process_email(email, now=now)
        assert result is None

    def test_day_7_action_generated(self):
        email = self._email("2026-07-01T10:00:00Z")
        now = datetime(2026, 7, 9, tzinfo=timezone.utc)  # 8 days after
        result = lib.process_email(email, now=now)
        assert result is not None
        assert result["stage"] == "day_7_nudge"
        # 7-9 (Jul 1 10:00 → Jul 9 00:00) = 7 days 14h, .days == 7
        assert result["days_since_sent"] == 7
        assert "Re: " in result["subject"]
        assert "Aramco" in result["body"]

    def test_day_14_action_generated(self):
        email = self._email("2026-07-01T10:00:00Z")
        now = datetime(2026, 7, 16, tzinfo=timezone.utc)  # 15 days
        result = lib.process_email(email, now=now)
        assert result is not None
        assert result["stage"] == "day_14_followup"

    def test_day_21_breakup(self):
        email = self._email("2026-07-01T10:00:00Z")
        now = datetime(2026, 7, 25, tzinfo=timezone.utc)  # 24 days
        result = lib.process_email(email, now=now)
        assert result["stage"] == "day_21_breakup"

    def test_missing_to_company_skips(self):
        email = self._email("2026-07-01T10:00:00Z")
        email["to"] = {}
        now = datetime(2026, 7, 9, tzinfo=timezone.utc)
        assert lib.process_email(email, now=now) is None

    def test_bad_sent_at_skips(self):
        email = self._email("not-a-date")
        now = datetime(2026, 7, 9, tzinfo=timezone.utc)
        assert lib.process_email(email, now=now) is None


# ================================================================
# run_sequencer
# ================================================================

class TestRunSequencer:
    def _emails(self, sent_dates: list) -> list:
        return [
            {
                "to": {"company": f"Co-{i}", "contact": "Buyer", "country": "US"},
                "subject": f"Email {i}",
                "body": "...",
                "language": "en",
                "product_category": "OCTG",
                "sent_at": d,
            }
            for i, d in enumerate(sent_dates)
        ]

    def test_summary(self):
        now = datetime(2026, 7, 18, tzinfo=timezone.utc)
        # 3 sent at different days → different stages
        emails = self._emails([
            "2026-07-15T10:00:00Z",  # 3 days → pending
            "2026-07-09T10:00:00Z",  # 9 days → day_7
            "2026-07-01T10:00:00Z",  # 17 days → day_14
            "2026-06-25T10:00:00Z",  # 23 days → day_21
        ])
        report = lib.run_sequencer(emails, now=now)
        assert report["summary"]["total_emails"] == 4
        assert report["summary"]["actions_due"] == 3
        assert report["summary"]["by_stage"]["day_7_nudge"] == 1
        assert report["summary"]["by_stage"]["day_14_followup"] == 1
        assert report["summary"]["by_stage"]["day_21_breakup"] == 1
        assert report["summary"]["pending"] == 1

    def test_empty_input(self):
        report = lib.run_sequencer([])
        assert report["summary"]["total_emails"] == 0
        assert report["summary"]["actions_due"] == 0

    def test_input_must_be_list(self):
        with pytest.raises(lib.InvalidEmailRecord):
            lib.run_sequencer("not a list")

    def test_invalid_email_collected(self):
        emails = [
            {"to": {}, "sent_at": "2026-07-01T10:00:00Z"},  # missing company → skip (not error)
            {"to": {"company": "X"}, "sent_at": "bad-date"},  # bad date → error
        ]
        now = datetime(2026, 7, 9, tzinfo=timezone.utc)
        report = lib.run_sequencer(emails, now=now)
        # missing company is silently skipped (not in errors[]); bad date is an error
        assert report["summary"]["errors"] == 1
        assert report["summary"]["actions_due"] == 0

    def test_output_schema_keys(self):
        report = lib.run_sequencer([])
        for k in ("$schema", "report_date_utc", "summary", "actions", "errors"):
            assert k in report

    def test_action_keys(self):
        email = {
            "to": {"company": "Aramco", "contact": "Mr. A", "country": "SA"},
            "subject": "Initial outreach",
            "body": "...",
            "language": "es",
            "product_category": "OCTG casing",
            "sent_at": "2026-07-01T10:00:00Z",
        }
        now = datetime(2026, 7, 9, tzinfo=timezone.utc)
        report = lib.run_sequencer([email], now=now)
        assert len(report["actions"]) == 1
        a = report["actions"][0]
        for k in ("buyer", "contact", "country", "stage", "days_since_sent",
                   "subject", "body", "language"):
            assert k in a
        # Spanish body
        assert "Estimado" in a["body"]
        assert a["language"] == "es"
