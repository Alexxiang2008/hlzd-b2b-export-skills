# HLZD Extensions to last30days (fork-specific documentation)

> This file documents everything HLZD added on top of upstream `mvanhorn/last30days-skill`.
> Read this to understand the fork's HLZD layer without diffing against upstream.

## Fork overview

- **Upstream**: [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) v3.11.0 (MIT)
- **HLZD layer**: pain-point extraction for B2B cross-border trade product research
- **Audience**: 深圳海联智达科技 B2B 跨境贸易老板 + 业务团队 (NOT market analysts)
- **Install**: `~/.claude/skills/hlzd-market-intel/` (flat layout)

## What HLZD changed (vs upstream)

### 1. SKILL.md frontmatter (KEEP OURS on sync)
- `name`: `hlzd-market-intel` (upstream is `last30days`)
- `description`: rewritten "Use when ..." format (~95 chars, high-frequency keywords: 调研/选品/客户痛点/跨境)
- `triggers`: 26 中英文 keywords (Panmira SkillRouter convention)
- `context: fork`, `agent: general-purpose` added
- Upstream `metadata.openclaw` block retained (openclaw ecosystem compat)
- Upstream body (2236 lines, 10 LAWs, setup wizard, Step 0-0.75) UNCHANGED on purpose — it is the anti-regression contract (each LAW records a verified 0/8 public regression). Do NOT "standardize" it away by splitting into references; that breaks sync and discards verified protection.

### 2. scripts/lib/pain_extractor.py (NEW file, HLZD-authored)
Top 5 customer pain-point extraction. Pure keyword-based (no LLM call, deterministic).
- `DEFAULT_TOPIC_CLUSTERS`: security-camera / smart-home profile (10 clusters) — the v0.1 default
- `extract(research_results, items_by_source, topic_clusters=None)`: main entry; `topic_clusters` injectable so other categories can override the default
- `load_topic_clusters(path)`: load a YAML/JSON profile (see `presets/pain-profiles/`)
- `_validate_topic_clusters(data)`: schema validation (id/label/keywords required)
- `run_pain_pipeline(args, research_results, items_by_source)`: full pipeline (extract + pain_output JSON write + inject into `research_results["pain_extraction"]`), idempotent; called by last30days.py
- `format_pain_section(pain_data)`: stderr rendering of the Top 5 section

### 3. scripts/last30days.py (HLZD integration; KEEP OURS on pain_extractor conflict)
- `--extract-pain` flag: enable pain extraction
- `--pain-output PATH` flag: write pain JSON to file
- Calls `pain_extractor.run_pain_pipeline()` (single extraction, cached)
- Renders `format_pain_section()` to stderr AFTER `compute_quality_score` (kept separate so quality scoring runs between inject and render)

### 4. assets/report-template-hlzd.html (KEEP OURS)
- HLZD brand gradient (deep blue → indigo → purple)
- Pain section CSS
- `assets/report-template-base.html` kept as upstream-style baseline

### 5. scripts/sync-from-upstream.sh (NEW, HLZD-authored)
- `git fetch upstream main && git merge --no-edit`
- `--dry-run` supported
- Conflict resolution rules (see "Sync rules" below)

## Core API (extending the fork)

### Add a new product category (smart locks, biomedical, 3C, outdoor gear, ...)

1. Create `presets/pain-profiles/<category>.yaml` (copy `security-camera.yaml` as template)
2. Load it: `clusters = pain_extractor.load_topic_clusters("presets/pain-profiles/<category>.yaml")`
3. Pass to extract: `pain_extractor.extract(research_results, items_by_source, topic_clusters=clusters)`
4. Use via CLI: `last30days.py "<topic>" --extract-pain --pain-profile presets/pain-profiles/<category>.yaml` (wired into `run_pain_pipeline`; the loaded profile overrides the default security-camera clusters)

### Pain profile schema
```yaml
- id: <kebab-case-id>           # required, non-empty string
  label: "<中英 label>"          # required, string
  keywords: ["kw1", "kw2", ...]  # required, non-empty list of non-empty strings
```
Pure-numeric keywords (e.g. `-80`) MUST be quoted, otherwise YAML parses them as ints and schema validation rejects them.

## Sync rules (sync-from-upstream.sh)

| Path | On conflict |
|---|---|
| `SKILL.md`, `README.md`, `assets/*` | KEEP OURS (HLZD version) |
| `scripts/lib/pain_extractor.py` | KEEP OURS (HLZD-authored, upstream has no such file — no conflict expected) |
| `scripts/lib/*.py` (other modules) | TAKE THEIRS (upstream) |
| `scripts/last30days.py` | TAKE THEIRS, except `pain_extractor` integration region (KEEP OURS) |
| `tests/test_pain_extractor.py` | KEEP OURS (HLZD test) |
| `tests/*.py` (upstream tests) | TAKE THEIRS |
| `references/hlzd-extensions.md` | KEEP OURS (this file) |
| `presets/pain-profiles/*` | KEEP OURS (HLZD profiles) |

## Known limitations (v0.1)

- Default pain profile is **security-camera / smart-home**. Other categories (smart locks, biomedical/exosomes, 3C) must pass a custom `topic_clusters` or load a profile via `load_topic_clusters()` — otherwise pains fall into wrong clusters or none.
- Pain extraction is **keyword-based, deterministic** (no LLM call). Quality depends on profile coverage. For the 5-dimension signal judgment, see `references/methodology.md` in the `b2b-overseas-market-report` sibling skill.
- `--pain-profile` selects ONE profile per run. Auto-detecting the category from the topic (e.g. "exosomes" → biomedical.yaml) is NOT implemented — the caller (user or LLM) passes the profile path explicitly. The SKILL.md `argument-hint` shows the `exosomes --pain-profile ...` example so the LLM discovers the pattern.
- Pain extraction reads only from `items_by_source`; if the engine returns zero items for a category (English-dominant sources, non-Latin topics), pains will be empty regardless of profile.

## Test baseline

- `tests/test_pain_extractor.py`: 16 tests (6 regression + 5 `load_topic_clusters` + 5 `run_pain_pipeline`), ~0.17s
- Run: `py -m pytest tests/test_pain_extractor.py -v` from fork root
- Upstream inherited tests: `python -m pytest tests/ -v` (2701/2735 pass, 34 upstream Windows-only failures)
