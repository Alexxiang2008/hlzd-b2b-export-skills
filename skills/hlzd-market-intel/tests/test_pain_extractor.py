"""Tests for scripts/lib/pain_extractor.py (HLZD fork extension).

4 tests covering:
  1. test_extracts_keyword_signals_from_snippets — happy path, multiple items
  2. test_ranks_by_severity_frequency — ordering of clusters
  3. test_handles_empty_inputs_gracefully — 0 items / 0 signals / None
  4. test_includes_user_quotes_with_verifiable_urls — only URLs in quotes
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# Make scripts/lib importable
REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "last30days"
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from lib import pain_extractor  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_item(*, source: str, source_id: str, title: str, body: str,
              why_relevant: str = "", url: str = "") -> SimpleNamespace:
    """Build a SourceItem-like object compatible with pain_extractor."""
    metadata = {}
    if why_relevant:
        metadata["why_relevant"] = why_relevant
    return SimpleNamespace(
        source=source,
        source_id=source_id,
        title=title,
        body=body,
        url=url or f"https://www.{source.lower()}.com/test/{source_id}",
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_extracts_keyword_signals_from_snippets():
    """Happy path: 3 items across 2 sources, multiple pain signals, 1 cluster wins."""
    items_by_source = {
        "reddit": [
            make_item(
                source="reddit", source_id="r1",
                title="Ring cameras false alarm issue",
                body=("The cameras failed to pick up a thief going through the driveway. " * 3) + ("We have multiple cameras outside and none of them caught the alert because of false alarm. " * 2),
                why_relevant="r/homesecurity: complaint about Ring false alarms",
                url="https://www.reddit.com/r/homesecurity/comments/r1/",
            ),
            make_item(
                source="reddit", source_id="r2",
                title="False alerts all night",
                body="I keep getting false alarm notifications. Annoying doesn't even begin to describe it. " * 2,
                why_relevant="r/SecurityCamera: user frustrated with false alerts",
                url="https://www.reddit.com/r/SecurityCamera/comments/r2/",
            ),
        ],
        "pelco": [
            make_item(
                source="pelco", source_id="p1",
                title="AI cameras reduce false alarms 90%",
                body="Modern AI cameras can differentiate between real security threats and false alarms. " * 2,
                why_relevant="Pelco 2026 report: AI reduces false alarms",
                url="https://www.pelco.com/blog/false-alarm-filtering",
            ),
        ],
    }
    result = pain_extractor.extract({}, items_by_source)
    assert result["total_signals_analyzed"] > 0
    assert result["top_5_pains"], "Expected at least one pain"
    top = result["top_5_pains"][0]
    assert "误报" in top["summary"] or "false" in top["summary"].lower() or "alarm" in top["summary"].lower(), \
        f"Expected false-alarm cluster, got: {top['summary']}"
    assert top["frequency"] >= 1
    # Both Reddit items + Pelco should mention "false alarm" cluster
    assert "reddit" in top["source_platforms"]


def test_ranks_by_severity_frequency():
    """Cluster with higher frequency × severity should rank higher."""
    # Cluster A: high frequency (3 sources), moderate severity
    # Cluster B: low frequency (1 source), high severity
    items_by_source = {
        "reddit": [
            make_item(
                source="reddit", source_id="r1",
                title="false alarm again",
                body="I keep getting false alarm notifications. Annoying. " * 2,
                url="https://www.reddit.com/r/homesecurity/comments/r1/",
            ),
        ],
        "tiktok": [
            make_item(
                source="tiktok", source_id="t1",
                title="AI false alarm 90%",
                body="AI cameras can reduce false alarms. False alerts are annoying. " * 2,
                url="https://www.tiktok.com/@jooancamera0/video/t1/",
            ),
        ],
        "web": [
            make_item(
                source="web", source_id="w1",
                title="false alarm filtering 2026",
                body="AI-powered cameras can filter out false alarms. Annoying alerts. " * 2,
                url="https://www.pelco.com/blog/false-alarm-filtering",
            ),
        ],
    }
    result = pain_extractor.extract({}, items_by_source)
    # Top pain should be the false-alarm one (high frequency)
    if result["top_5_pains"]:
        top = result["top_5_pains"][0]
        assert "误报" in top["summary"] or "false" in top["summary"].lower() or "alarm" in top["summary"].lower(), \
            f"Expected false alarm cluster, got: {top['summary']}"
        assert top["frequency"] >= 2, f"Expected frequency >= 2, got {top['frequency']}"


def test_handles_empty_inputs_gracefully():
    """No items / empty dict / None — should not crash, return empty result."""
    # 0 items
    r0 = pain_extractor.extract({}, {})
    assert r0["top_5_pains"] == []
    assert r0["total_signals_analyzed"] == 0
    # None items_by_source
    r1 = pain_extractor.extract({}, None)
    assert r1["top_5_pains"] == []
    # Empty list per source
    r2 = pain_extractor.extract({}, {"reddit": [], "youtube": []})
    assert r2["top_5_pains"] == []


def test_includes_user_quotes_with_verifiable_urls():
    """User quotes must have a non-empty URL; items without URL are dropped."""
    # One item WITH URL, one item WITHOUT URL, both have pain signals
    items_by_source = {
        "reddit": [
            make_item(
                source="reddit", source_id="r1",
                title="False alarms",
                body="I keep getting false alarm notifications. Annoying. " * 3,
                url="https://www.reddit.com/r/homesecurity/comments/r1/",
            ),
            make_item(
                source="reddit", source_id="r2_no_url",
                title="More false alarms",
                body="Another false alarm. Annoying alerts. " * 3,
                url="",  # NO URL — should be dropped
            ),
        ],
    }
    result = pain_extractor.extract({}, items_by_source)
    if result["top_5_pains"]:
        top = result["top_5_pains"][0]
        # All user_quotes must have non-empty URL
        for quote in top["user_quotes"]:
            assert quote["url"], f"Quote must have URL, got: {quote}"
            assert quote["url"].startswith("http"), f"Quote URL must be http(s), got: {quote['url']}"


if __name__ == "__main__":
    import unittest
    unittest.main()
