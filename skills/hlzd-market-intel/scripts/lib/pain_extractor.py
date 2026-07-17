"""Pain extraction layer for hlzd-market-intel fork.

Extracts the Top 5 customer pain points from the last30days engine output,
for the HLZD "跨境贸易" report use case. Pure keyword-based extraction —
no extra LLM call, deterministic, testable. Output is JSON-shaped so
`quality_nudge.py` can render it as a "Top 5 pains" section.

The extraction strategy:
  1. Pull all evidence texts (title + body + why_relevant) from items_by_source
  2. Match pain keyword patterns (multilingual: EN + ZH)
  3. Cluster matches into pain topics by co-occurrence of keyword groups
  4. Score each cluster: frequency (distinct sources) × severity (strong-pain density)
  5. Pick top 5, attach 1-2 user quotes per pain (verifiable URL only)
  6. Return JSON-shaped output

This is a heuristic, not a rigorous framework. See `references/methodology.md`
in `b2b-overseas-market-report` for the full 5-dimension signal judgment
that the upstream `quality_nudge.py` uses.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Pain keyword patterns (multilingual)
# ---------------------------------------------------------------------------

# Tier 1 — strong pain signals (high severity, weight 3)
STRONG_PAIN_PATTERNS = [
    r"\bbroke[n]?\b",
    r"\bbroken\b",
    r"\bdoesn['’]?t work",
    r"\bcan['’]?t (?:even |just )?(?:use|install|setup|configure)",
    r"\b(?:annoying|frustrat\w*|terrible|awful|horrible|useless|garbage|trash|crap)\b",
    r"\b(?:pain|problem|issue|bug|crash|fail\w*|error)\b",
    r"\b(?:return|refund|disappoint\w*|regret|complain\w*)\b",
    r"\bhate\b",
    r"\bdead (?:on arrival|out of the box)\b",
    r"\b(?:头疼|不行|难用|垃圾|坑|翻车|踩雷)\b",
]

# Tier 2 — moderate pain signals (weight 2)
MODERATE_PAIN_PATTERNS = [
    r"\b(?:missing|lack\w*|no \w+ option|wish (?:it (?:had|supported))?)\b",
    r"\b(?:confus\w*|overwhelm\w*|complicated|too (?:complex|hard|difficult))\b",
    r"\b(?:slow|laggy|lag\w*|freeze|hang|buggy|glitch\w*)\b",
    r"\b(?:expensive|overprice|pricey|too much|not worth)\b",
    r"\b(?:subscription|monthly|recurring|hidden cost|fee)\b",
    r"\b(?:should have|why (?:isn['’]?t|doesn['’]?t)|if only)\b",
    r"\b(?:麻烦|不太行|贵|坑|累|烦)\b",
]

# Tier 3 — feature-desire / pain-adjacent (weight 1)
DESIRE_PATTERNS = [
    r"\b(?:I wish|would be (?:nice|great)|if (?:only|they))",
    r"\b(?:hope(?:ful)?|want|need|looking for|searching for)\b",
    r"\b(?:alternative|alternative to|replacement|instead of)\b",
    r"\b(?:suggestion|recommend|suggest|any (?:good )?(?:alternative|option))\b",
    r"\b(?:求|推荐|想要|换|替代)\b",
]

# Compile once
_STRONG_RE = re.compile("|".join(STRONG_PAIN_PATTERNS), re.IGNORECASE)
_MODERATE_RE = re.compile("|".join(MODERATE_PAIN_PATTERNS), re.IGNORECASE)
_DESIRE_RE = re.compile("|".join(DESIRE_PATTERNS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# Topic clustering — lightweight keyword affinity
# ---------------------------------------------------------------------------

# Each cluster is a set of related keywords. Multiple clusters can match
# the same item; the strongest cluster wins.
#
# v0.1 ships a SECURITY CAMERA / smart-home default profile. To support
# another category (smart locks, 3C accessories, outdoor gear, ...), pass
# a custom `topic_clusters` list to extract(). The load_topic_clusters()
# stub below is the future YAML-loading extension point.
DEFAULT_TOPIC_CLUSTERS: List[Dict[str, Any]] = [
    {
        "id": "false_alarms",
        "label": "误报 / false alerts",
        "keywords": ["false alarm", "false alert", "motion alert", "person alert",
                     "vehicle alert", "notification", "误报", "提醒", "警报"],
    },
    {
        "id": "subscription_cost",
        "label": "订阅费 / subscription",
        "keywords": ["subscription", "monthly fee", "monthly", "recurring",
                     "cloud storage", "付费", "订阅", "月费"],
    },
    {
        "id": "installation",
        "label": "安装 / setup",
        "keywords": ["install", "setup", "configuration", "wireless",
                     "wired", "cable", "install", "安装"],
    },
    {
        "id": "video_quality",
        "label": "画质 / video quality",
        "keywords": ["4k", "1080p", "resolution", "video quality",
                     "night vision", "color night", "清晰度", "画质"],
    },
    {
        "id": "ai_smart",
        "label": "AI 检测 / smart detection",
        # NOTE: use compound keywords (not bare "ai") to avoid false positives
        # on words like "becAISE", "trAIl", "aImed" that contain "ai" as a
        # substring. Compound phrases like "ai camera", "ai detection",
        # "on-device ai" are the actual product-feature vocabulary.
        "keywords": ["ai camera", "ai detection", "on-device ai", "ai feature",
                     "ai alert", "smart detection", "person detection",
                     "vehicle detection", "package detection", "face recognition",
                     "智能检测", "AI 检测", "人形检测"],
    },
    {
        "id": "ecosystem_integration",
        "label": "生态整合 / ecosystem",
        "keywords": ["alexa", "google home", "homekit", "rtsp", "onvif",
                     "synology", "frigate", "home assistant", "兼容",
                     "对接"],
    },
    {
        "id": "privacy_security",
        "label": "隐私 / privacy",
        "keywords": ["privacy", "data", "cloud", "local", "self-host",
                     "隐私", "本地", "数据"],
    },
    {
        "id": "battery_power",
        "label": "电池 / power",
        "keywords": ["battery", "solar", "wireless", "recharge",
                     "电池", "续航", "太阳能"],
    },
    {
        "id": "build_quality",
        "label": "做工 / build quality",
        "keywords": ["build quality", "plastic", "cheap", "broken hinge",
                     "做工", "塑料"],
    },
    {
        "id": "app_experience",
        "label": "App 体验 / app",
        "keywords": ["app", "ui", "ux", "notification", "load time",
                     "crash", "界面", "卡顿"],
    },
]


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def _extract_text_blob(item) -> str:
    """Concatenate title + body + why_relevant + any metadata text fields."""
    parts = []
    title = getattr(item, "title", None) or (item.get("title") if isinstance(item, dict) else "")
    body = getattr(item, "body", None) or (item.get("body") if isinstance(item, dict) else "")
    if title:
        parts.append(str(title))
    if body:
        parts.append(str(body))
    # metadata fields
    metadata = getattr(item, "metadata", None) or (item.get("metadata") if isinstance(item, dict) else {})
    if isinstance(metadata, dict):
        why = metadata.get("why_relevant")
        if why:
            parts.append(str(why))
        # Also pull snippet from evidence-like keys
        for key in ("snippet", "description", "transcript_highlights"):
            v = metadata.get(key)
            if v:
                parts.append(str(v))
    return "\n".join(parts)


def _match_pain_signals(text: str) -> Dict[str, int]:
    """Return counts of strong / moderate / desire pain signals in text."""
    return {
        "strong": len(_STRONG_RE.findall(text)),
        "moderate": len(_MODERATE_RE.findall(text)),
        "desire": len(_DESIRE_RE.findall(text)),
    }


def _match_topic_clusters(text: str, clusters: Optional[List[Dict[str, Any]]] = None) -> Set[str]:
    """Return set of topic cluster IDs that the text matches.

    `clusters` defaults to DEFAULT_TOPIC_CLUSTERS (security-camera profile)
    when None; pass a custom list to support a different product category.
    """
    if clusters is None:
        clusters = DEFAULT_TOPIC_CLUSTERS
    text_lower = text.lower()
    matched = set()
    for cluster in clusters:
        for kw in cluster["keywords"]:
            if kw.lower() in text_lower:
                matched.add(cluster["id"])
                break
    return matched


def _severity_score(pain_counts: Dict[str, int]) -> float:
    """Compute severity score from pain signal counts (1-5 scale)."""
    strong = pain_counts["strong"]
    moderate = pain_counts["moderate"]
    desire = pain_counts["desire"]
    raw = strong * 3 + moderate * 2 + desire
    # Map raw score to 1-5 scale
    if raw >= 8:
        return 5
    elif raw >= 5:
        return 4
    elif raw >= 3:
        return 3
    elif raw >= 1:
        return 2
    return 1


def _pick_user_quotes(items, topic_id: str, clusters: Optional[List[Dict[str, Any]]] = None, top_n: int = 2) -> List[Dict[str, str]]:
    """Pick 1-2 user quotes from items that match the given topic_id.

    Each quote MUST have a verifiable URL (no URL → quote is dropped).
    `clusters` defaults to DEFAULT_TOPIC_CLUSTERS when None.
    """
    if clusters is None:
        clusters = DEFAULT_TOPIC_CLUSTERS
    quotes = []
    cluster_keywords = next(
        (c["keywords"] for c in clusters if c["id"] == topic_id), []
    )
    cluster_lower = [k.lower() for k in cluster_keywords]

    for item in items:
        text = _extract_text_blob(item)
        text_lower = text.lower()
        if not any(kw in text_lower for kw in cluster_lower):
            continue

        url = getattr(item, "url", None) or (item.get("url") if isinstance(item, dict) else None)
        if not url:
            continue

        # Extract a representative sentence (first sentence containing a pain keyword)
        quote_text = _extract_representative_sentence(text, cluster_keywords)
        if not quote_text:
            continue

        source = getattr(item, "source", None) or (item.get("source") if isinstance(item, dict) else None)
        quotes.append({
            "platform": source or "Unknown",
            "url": url,
            "text": quote_text[:400],  # cap to keep file size reasonable
        })
        if len(quotes) >= top_n:
            break
    return quotes


def _extract_representative_sentence(text: str, cluster_keywords: List[str]) -> str:
    """Find the first sentence in `text` that contains any cluster keyword."""
    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(kw.lower() in sentence_lower for kw in cluster_keywords):
            cleaned = sentence.strip()
            if len(cleaned) >= 20:  # skip very short fragments
                return cleaned
    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_topic_clusters(path: str) -> List[Dict[str, Any]]:
    """Load a custom topic_clusters profile from a YAML or JSON file.

    Format is selected by file extension:
      .json         -> stdlib json (no extra dependency)
      .yaml / .yml  -> PyYAML (pip install pyyaml)

    File format (YAML example):
      - id: battery_life
        label: "电池续航 / battery life"
        keywords: ["battery life", "battery", "续航"]
      - id: fingerprint
        label: "指纹识别 / fingerprint"
        keywords: ["fingerprint", "指纹", "unlock"]

    Each cluster must have: id (non-empty str), label (str),
    keywords (non-empty list[str]). See _validate_topic_clusters.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"topic clusters file not found: {path}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise ImportError(
                "PyYAML is required to load YAML pain profiles "
                "(pip install pyyaml). JSON profiles need no extra dependency."
            ) from exc
        data = yaml.safe_load(text)
    else:
        raise ValueError(
            f"unsupported topic clusters file extension '{suffix}' "
            "(use .json, .yaml, or .yml)"
        )
    return _validate_topic_clusters(data)


def _validate_topic_clusters(data: Any) -> List[Dict[str, Any]]:
    """Validate the schema of a loaded topic_clusters list.

    Returns the data unchanged if valid; raises ValueError with a precise
    message otherwise.
    """
    if not isinstance(data, list):
        raise ValueError(
            f"topic clusters file must contain a list at top level, "
            f"got {type(data).__name__}"
        )
    if not data:
        raise ValueError("topic clusters list is empty")
    required_fields = {"id", "label", "keywords"}
    for i, cluster in enumerate(data):
        if not isinstance(cluster, dict):
            raise ValueError(f"cluster[{i}] must be a dict, got {type(cluster).__name__}")
        missing = required_fields - set(cluster.keys())
        if missing:
            raise ValueError(f"cluster[{i}] missing required fields: {sorted(missing)}")
        if not isinstance(cluster["id"], str) or not cluster["id"].strip():
            raise ValueError(f"cluster[{i}].id must be a non-empty string")
        if not isinstance(cluster["label"], str):
            raise ValueError(f"cluster[{i}].label must be a string")
        kws = cluster["keywords"]
        if not isinstance(kws, list) or not kws:
            raise ValueError(f"cluster[{i}].keywords must be a non-empty list")
        for kw in kws:
            if not isinstance(kw, str) or not kw.strip():
                raise ValueError(
                    f"cluster[{i}].keywords contains a non-string or empty entry"
                )
    return data


def run_pain_pipeline(args, research_results: dict, items_by_source: Optional[dict]) -> Optional[dict]:
    """Run the full pain-extraction pipeline for the last30days engine.

    Centralizes what last30days.py needs around pain extraction:
      1. load --pain-profile YAML/JSON if given (overrides default profile)
      2. extract() the Top 5 pains (with the resolved topic clusters)
      3. write --pain-output JSON if requested
      4. inject pain_data into research_results["pain_extraction"] so
         quality_nudge can read it

    Returns the pain_data dict (possibly with empty top_5_pains), or None
    if --extract-pain is not set or extraction failed. The caller renders
    format_pain_section() to stderr AFTER compute_quality_score — kept
    separate so quality scoring runs between inject and render.

    Idempotent: if research_results["pain_extraction"] is already set,
    returns the cached value without re-extracting.
    """
    if not getattr(args, "extract_pain", False):
        return None
    cached = research_results.get("pain_extraction")
    if cached is not None:
        return cached
    try:
        # Load a custom topic-cluster profile if --pain-profile was given;
        # overrides DEFAULT_TOPIC_CLUSTERS (security camera) so non-安防
        # categories (biomedical, 3C, ...) get correct pain clustering.
        topic_clusters = None
        profile_path = getattr(args, "pain_profile", None)
        if profile_path:
            topic_clusters = load_topic_clusters(profile_path)
            sys.stderr.write(
                f"[last30days] Loaded pain profile: {profile_path} "
                f"({len(topic_clusters)} clusters)\n"
            )
        pain_data = extract(research_results, items_by_source, topic_clusters=topic_clusters)
        pain_output = getattr(args, "pain_output", None)
        if pain_output:
            with open(pain_output, "w", encoding="utf-8") as f:
                json.dump(pain_data, f, ensure_ascii=False, indent=2)
            sys.stderr.write(
                f"[last30days] Pain extraction JSON written to {pain_output}\n"
            )
        if pain_data.get("top_5_pains"):
            research_results["pain_extraction"] = pain_data
        return pain_data
    except Exception as exc:
        sys.stderr.write(f"[last30days] Pain extraction failed: {exc}\n")
        return None


def extract(research_results: dict, items_by_source: Optional[dict] = None, topic_clusters: Optional[List[Dict[str, Any]]] = None) -> dict:
    """Extract Top 5 customer pain points from last30days engine output.

    Args:
        research_results: aggregate metrics from last30days.py main().
            Currently used only for metadata (timestamp); pain extraction
            reads from items_by_source.
        items_by_source: dict mapping source name to list of SourceItem
            (or dicts) from `report.items_by_source`. Optional for backward
            compat — if None, returns empty top_5_pains.
        topic_clusters: optional list of cluster dicts (each with id/label/
            keywords) overriding DEFAULT_TOPIC_CLUSTERS. v0.1 defaults to the
            security-camera / smart-home profile; pass a custom list to
            support another product category. See load_topic_clusters() for
            the future YAML extension point.

    Returns:
        JSON-shaped dict with `top_5_pains` list. Schema:

        {
            "extraction_timestamp": "2026-07-07T16:00:00Z",
            "extraction_method": "keyword+llm-stub",
            "total_signals_analyzed": 312,
            "top_5_pains": [
                {
                    "rank": 1,
                    "summary": "<1-2 sentence pain description>",
                    "severity": 5,
                    "frequency": 4,
                    "source_platforms": ["Reddit", "Pelco"],
                    "user_quotes": [{"platform": "Reddit", "url": "...", "text": "..."}],
                },
                ...
            ]
        }
    """
    if not items_by_source:
        return {
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "extraction_method": "keyword+llm-stub",
            "total_signals_analyzed": 0,
            "top_5_pains": [],
        }

    # Resolve the topic-cluster profile (v0.1 default = security camera).
    profile = topic_clusters if topic_clusters is not None else DEFAULT_TOPIC_CLUSTERS

    # Phase 1: collect all items with pain signals + topic clusters
    cluster_to_items = defaultdict(list)  # cluster_id -> [(item, severity)]
    total_signals = 0

    for source, items in items_by_source.items():
        for item in items:
            text = _extract_text_blob(item)
            if not text:
                continue
            pain_counts = _match_pain_signals(text)
            total_signals += sum(pain_counts.values())
            if sum(pain_counts.values()) == 0:
                continue
            clusters = _match_topic_clusters(text, profile)
            for cluster_id in clusters:
                severity = _severity_score(pain_counts)
                cluster_to_items[cluster_id].append((item, severity, source))

    # Phase 2: rank clusters by frequency × severity
    cluster_scores = []
    for cluster_id, item_severities in cluster_to_items.items():
        # frequency = # of distinct sources that mentioned this pain
        distinct_sources = {src for _, _, src in item_severities}
        frequency = len(distinct_sources)
        # avg severity across items in this cluster
        avg_severity = sum(s for _, s, _ in item_severities) / max(1, len(item_severities))
        # composite score (severity weighted more than frequency)
        score = avg_severity * 2 + frequency
        cluster_scores.append((cluster_id, score, frequency, avg_severity, item_severities))

    # Sort by score descending
    cluster_scores.sort(key=lambda x: -x[1])
    top_5 = cluster_scores[:5]

    # Phase 3: build the output
    top_5_pains = []
    for rank, (cluster_id, _, frequency, avg_severity, item_severities) in enumerate(top_5, 1):
        cluster_label = next(
            (c["label"] for c in profile if c["id"] == cluster_id), cluster_id
        )
        # Dedupe items by id
        seen_ids = set()
        deduped_items = []
        for it, sev, src in item_severities:
            it_id = getattr(it, "source_id", None) or (it.get("source_id") if isinstance(it, dict) else None) or id(it)
            if it_id in seen_ids:
                continue
            seen_ids.add(it_id)
            deduped_items.append(it)
        # Pick user quotes
        user_quotes = _pick_user_quotes(deduped_items, cluster_id, profile, top_n=2)
        # Platforms represented
        platforms = sorted({src for _, _, src in item_severities})
        # Summary: cluster label + frequency
        summary = f"{cluster_label} — {frequency} 个独立信源提及"
        if user_quotes:
            summary += f",典型用户原话:\"{user_quotes[0]['text'][:80]}...\""
        top_5_pains.append({
            "rank": rank,
            "summary": summary,
            "severity": round(avg_severity, 1),
            "frequency": frequency,
            "source_platforms": platforms,
            "user_quotes": user_quotes,
        })

    return {
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "extraction_method": "keyword+llm-stub",
        "total_signals_analyzed": total_signals,
        "top_5_pains": top_5_pains,
    }


# ---------------------------------------------------------------------------
# Rendering helper (for stderr / console output)
# ---------------------------------------------------------------------------

def format_pain_section(pain_data: dict) -> str:
    """Render pain_extractor output as a human-readable stderr section.

    HLZD fork extension: prints the Top 5 customer pain points extracted
    from the last30days engine evidence, formatted for an executive audience.

    Format: each pain gets a rank, summary, severity (1-5), source platforms,
    and 1-2 user quotes with verifiable URLs.
    """
    lines = ["=== Top 5 Customer Pain Points (HLZD extraction) ===", ""]
    for pain in pain_data.get("top_5_pains", []):
        rank = pain.get("rank", "?")
        summary = pain.get("summary", "")
        severity = pain.get("severity", 0)
        frequency = pain.get("frequency", 0)
        platforms = ", ".join(pain.get("source_platforms", []))
        lines.append(
            f"#{rank}  (severity {severity}/5  |  {frequency} source{'s' if frequency != 1 else ''}  |  {platforms})"
        )
        lines.append(f"     {summary}")
        for quote in pain.get("user_quotes", [])[:2]:
            platform = quote.get("platform", "?")
            url = quote.get("url", "")
            text = quote.get("text", "")[:200]
            ellipsis = "..." if len(quote.get("text", "")) > 200 else ""
            lines.append(f"     > [{platform}] {text}{ellipsis}")
            lines.append(f"       {url}")
        lines.append("")
    if not pain_data.get("top_5_pains"):
        lines.append("(no pain signals extracted)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry (for ad-hoc invocation)
# ---------------------------------------------------------------------------

def main() -> int:
    """CLI: read JSON research_results from stdin, emit JSON pain extraction to stdout."""
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        print("Usage: pipe JSON research_results to pain_extractor.py", file=sys.stderr)
        return 2
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON input: {exc}", file=sys.stderr)
        return 1
    # payload may be {research_results: {...}, items_by_source: {...}}
    research_results = payload.get("research_results", {})
    items_by_source = payload.get("items_by_source", {})
    out = extract(research_results, items_by_source)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
