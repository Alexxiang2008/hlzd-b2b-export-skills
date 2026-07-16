"""hlzd-followup-sequencer shared library.

Based on cold-outreach output (the first email record) + sent_at timestamp,
generate Day 7 / Day 14 follow-up drafts when appropriate.

Logic per email:
  < 7 days: not yet (pending)
  7-13 days: Day 7 nudge
  14-20 days: Day 14 follow-up
  >= 21 days: Day 21 break-up (or close)

Output: a report with summary + per-buyer actions to take today.
"""
from __future__ import annotations

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


def get_logger(name: str = "hlzd-followup-sequencer") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# 错误归类
# ================================================================

class FollowupError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-followup-sequencer",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


class InvalidEmailRecord(FollowupError):
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


# ================================================================
# Stage thresholds
# ================================================================

# Days-since-sent → stage mapping
# boundaries (lo, hi_inclusive)
STAGE_THRESHOLDS: List[Tuple[int, int, str]] = [
    (0, 6, "pending"),         # < 7
    (7, 13, "day_7_nudge"),
    (14, 20, "day_14_followup"),
    (21, 10_000, "day_21_breakup"),
]


# ================================================================
# Follow-up templates (per stage)
# 复用 cold-outreach 的模板风格, 调短 + 不再"hi from"
# ================================================================

FOLLOWUP_TEMPLATES = {
    "en": {
        "day_7_nudge": {
            "subject_prefix": "Re: ",
            "body": (
                "Hi {contact_name},\n\n"
                "Following up on my note last week about {product_category} for {recipient_company}. "
                "If the timing isn't right, no problem — just let me know whether to revisit in a quarter.\n\n"
                "Best regards,\n{sender_name}\n{sender_title} | {sender_company}\n"
                "{sender_email} | {sender_phone}"
            ),
        },
        "day_14_followup": {
            "subject_prefix": "Re: ",
            "body": (
                "Hi {contact_name},\n\n"
                "I followed up last week and want to make sure my message didn't get lost. "
                "If {recipient_company} is sourcing {product_category} over the next quarter, "
                "a 15-minute call would let me share specs and lead times.\n\n"
                "Best regards,\n{sender_name}\n{sender_title} | {sender_company}\n"
                "{sender_email} | {sender_phone}"
            ),
        },
        "day_21_breakup": {
            "subject_prefix": "Re: ",
            "body": (
                "Hi {contact_name},\n\n"
                "Closing the loop on my {product_category} notes for {recipient_company}. "
                "If now isn't the right time, I'll reach out again in a quarter. "
                "Wishing you a productive season.\n\n"
                "Best,\n{sender_name}"
            ),
        },
    },
    "es": {
        "day_7_nudge": {
            "subject_prefix": "Re: ",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Dando seguimiento a mi nota de la semana pasada sobre {product_category} "
                "para {recipient_company}. Si el momento no es oportuno, está bien — "
                "indiqueme si conviene revisar en un trimestre.\n\n"
                "Cordialmente,\n{sender_name}\n{sender_title} | {sender_company}\n"
                "{sender_email} | {sender_phone}"
            ),
        },
        "day_14_followup": {
            "subject_prefix": "Re: ",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Hice seguimiento la semana pasada y quiero asegurarme de que mi mensaje "
                "no se perdio. Si {recipient_company} esta en busqueda de {product_category} "
                "el proximo trimestre, una llamada de 15 minutos me permitiria compartir "
                "especificaciones y plazos.\n\n"
                "Cordialmente,\n{sender_name}\n{sender_title} | {sender_company}\n"
                "{sender_email} | {sender_phone}"
            ),
        },
        "day_21_breakup": {
            "subject_prefix": "Re: ",
            "body": (
                "Estimado/a {contact_name},\n\n"
                "Cierro el hilo sobre mis notas de {product_category} para {recipient_company}. "
                "Si no es buen momento, contactare nuevamente en un trimestre. "
                "Le deseo una temporada productiva.\n\n"
                "Cordialmente,\n{sender_name}"
            ),
        },
    },
}


# ================================================================
# Helpers
# ================================================================

def parse_iso_date(s: str) -> datetime:
    """宽松 ISO 解析: 'YYYY-MM-DD' / 'YYYY-MM-DDTHH:MM:SSZ' / with +00:00"""
    if not s:
        raise InvalidEmailRecord("missing sent_at")
    s = s.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    raise InvalidEmailRecord(f"bad sent_at format: {s!r}")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def days_since(dt: datetime, *, now: Optional[datetime] = None) -> int:
    if now is None:
        now = now_utc()
    delta = now - dt
    return delta.days


def stage_for_days(days: int) -> str:
    for lo, hi, stage in STAGE_THRESHOLDS:
        if lo <= days <= hi:
            return stage
    return "pending"  # future-dated (negative days)


def pick_template(stage: str, language: str = "en") -> Optional[Dict[str, str]]:
    lang_templates = FOLLOWUP_TEMPLATES.get(language, FOLLOWUP_TEMPLATES.get("en"))
    return lang_templates.get(stage)


def fill_placeholders(text: str, variables: Dict[str, Any]) -> str:
    def _sub(m):
        key = m.group(1)
        if key not in variables or variables[key] is None:
            return m.group(0)  # leave placeholder
        return str(variables[key])
    return re.sub(r"\{(\w+)\}", _sub, text)


# ================================================================
# Per-email processing
# ================================================================

def process_email(email: Dict[str, Any], *,
                   now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Return a follow-up action dict, or None if no action needed yet.

    Returns dict with keys:
      buyer, country, contact, stage, days_since_sent,
      subject, body, source_sent_at
    """
    if not isinstance(email, dict):
        raise InvalidEmailRecord("email must be a dict")

    to = email.get("to", {}) or {}
    company = to.get("company", "")
    contact = to.get("contact", "")
    country = to.get("country", "")
    if not company:
        return None  # skip malformed

    sent_at_str = email.get("sent_at", "")
    try:
        sent_at = parse_iso_date(sent_at_str)
    except InvalidEmailRecord:
        return None

    days = days_since(sent_at, now=now)
    stage = stage_for_days(days)
    if stage == "pending":
        return None  # not yet due

    language = email.get("language", "en")
    template = pick_template(stage, language)
    if template is None:
        return None  # no template for this stage/lang

    # subject from original (Re: prefix)
    original_subject = email.get("subject", "")
    subject = template["subject_prefix"] + original_subject

    # build variables
    product_category = email.get("product_category", "industrial equipment")
    variables = {
        "contact_name": contact or "Procurement Team",
        "recipient_company": company,
        "product_category": product_category,
        "sender_name": email.get("sender_name", "Sales Team"),
        "sender_title": email.get("sender_title", "International Sales"),
        "sender_company": email.get("sender_company", "HLZD"),
        "sender_email": email.get("sender_email", "sales@hlzd.example"),
        "sender_phone": email.get("sender_phone", ""),
    }
    body = fill_placeholders(template["body"], variables)

    return {
        "buyer": company,
        "contact": contact,
        "country": country,
        "stage": stage,
        "days_since_sent": days,
        "source_sent_at": sent_at_str,
        "subject": subject,
        "body": body,
        "language": language,
    }


# ================================================================
# Pipeline main
# ================================================================

def run_sequencer(
    emails: List[Dict[str, Any]],
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Process a list of email records, return a follow-up report.

    Input list shape (typically the 'emails' field of cold-outreach output):
      [
        {"to": {...}, "subject": "...", "body": "...",
         "language": "en", "customer_type_used": "Manufacturer",
         "sent_at": "2026-07-01T10:00:00Z"},
        ...
      ]
    """
    if not isinstance(emails, list):
        raise InvalidEmailRecord("emails must be a list")

    actions: List[Dict[str, Any]] = []
    errors: List[str] = []
    by_stage: Dict[str, int] = {"day_7_nudge": 0, "day_14_followup": 0,
                                  "day_21_breakup": 0}
    pending = 0

    for i, email in enumerate(emails):
        try:
            action = process_email(email, now=now)
        except FollowupError as exc:
            errors.append(f"email {i}: {exc}")
            continue
        if action is None:
            # could be malformed or pending
            if not (email.get("to", {}) or {}).get("company"):
                errors.append(f"email {i}: missing 'to.company'")
            else:
                pending += 1
            continue
        actions.append(action)
        by_stage[action["stage"]] = by_stage.get(action["stage"], 0) + 1

    if now is None:
        now = now_utc()

    return {
        "$schema": "hlzd/followup-sequencer/v1",
        "report_date_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total_emails": len(emails),
            "actions_due": len(actions),
            "by_stage": by_stage,
            "pending": pending,
            "errors": len(errors),
        },
        "actions": actions,
        "errors": errors,
    }
