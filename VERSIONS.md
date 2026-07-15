# VERSIONS

## v0.4.0 — 2026-07-15

Fourth Skills batch. Repo version bumped 0.3.0 → 0.4.0 (new Skill added). W2-3 milestone now complete (4 of 21 Skills shipped).

### Skills

| Skill | Version | Notes |
|---|---|---|
| `hlzd-inquiry-qualify` | 0.1.0 | No change. 40 tests. |
| `hlzd-b2b-research` | 0.1.0 | No change. 31 tests. |
| `hlzd-buyer-finder` | 0.1.0 | No change. 45 tests. |
| `hlzd-market-report` | 0.1.0 | New. 9-section self-contained HTML report + 8-section Markdown. Voice contract LAWS (7 rules) implemented as executable checks in `lib.py` (offline-testable). `from_b2b_research()` adapter bridges hlzd-b2b-research JSON output to report schema. 41 tests. |

### Pipeline integration milestone

`hlzd-buyer-finder → hlzd-market-report` end-to-end flow now demonstrable:

```bash
# 1. Run market research (4-step pipeline)
py ../hlzd-b2b-research/scripts/run_research.py \
    --product "OCTG casing" --markets "UAE Saudi" \
    --output-json b2b-output.json

# 2. Convert to HTML report
py scripts/pipeline.py --topic "auto" \
    --from-research b2b-output.json \
    --output-html report.html --output-md report.md
```

### Architecture evolution

- `lib.py` introduces **executable LAWS** (functions like `check_law_1`, `check_law_2`, `validate_voice_contract`) — business rules now live alongside code, both usable by pipeline and by runtime validation
- `render_html.py` ships a **self-contained CSS** design system inspired by b2b-overseas-market-report's 63KB template but rebuilt for HLZD industrial-export aesthetic (deep blue + cyan accent)
- `assemble_report()` is **deterministic assembler** (no LLM); LLM enhancement (curated signals from raw) is left to upper-layer Agent
- `render_html.py` produces ~14 KB self-contained HTML (no external CSS / fonts / CDN)

### Verification

- `py validate_skills.py` → 4/4 OK
- Per-skill pytest:
  - `hlzd-inquiry-qualify`: 40/40
  - `hlzd-b2b-research`: 31/31
  - `hlzd-buyer-finder`: 45/45
  - `hlzd-market-report`: 41/41
- **Cumulative W2-3: 157 tests PASSED**
- Live `pipeline.run()` smoke test → produces valid 11-section report dictionary; renders 14 KB HTML + 4 KB Markdown on disk

---

## v0.3.0 — 2026-07-15

Third Skills batch. Repo version bumped from 0.2.0 → 0.3.0 (new Skill added).

### Skills

| Skill | Version | Notes |
|---|---|---|
| `hlzd-inquiry-qualify` | 0.1.0 | No change (v0.1.0 from W1). 40 tests / 85% coverage. |
| `hlzd-b2b-research` | 0.1.0 | No change (v0.1.0 from W2). 31 tests. |
| `hlzd-buyer-finder` | 0.1.0 | New. 3-link pipeline (Alibaba auto-discover competitors → Volza customs data → public directory fallback). 45 tests. Quotable determinism via Volza blocked-body detection (offline-testable). Cross-CLI quota persisted in `~/.cache/hlzd-buyer-finder/rate_state.json`. |

### Architecture evolution

- `lib.py` introduces two additive primitives: `RateLimiter` (interval + daily quota with state persistence) and `classify_volza_response` (deterministic 11055-byte detector for Volza anti-bot)
- All 3 source adapters (`alibaba.py` / `volza.py` / `keyword.py`) accept injectable `http_get` for testability
- `pipeline.py` exposes `volza_quota_override` / `alibaba_quota_override` / `alibaba_searcher` / `volza_searcher` kwargs for testing
- Money-string tolerant dedup: `_parse_money()` handles `"$1,234"`, `100 USD`, `500.0` etc.
- Mock target convention: tests patch `sources.X.Y` (not `pipeline.X.Y`) since pipeline uses lazy imports

### Verification

- `py validate_skills.py` → 3/3 OK
- Per-skill pytest:
  - `hlzd-inquiry-qualify`: 40/40
  - `hlzd-b2b-research`: 31/31
  - `hlzd-buyer-finder`: 45/45
- `cli.py --help` renders cleanly
- Live smoke test against real Alibaba + Volza: both blocked/captcha as expected; pipeline returns `warnings[]` and exits 1 (correct: "no importers found")

---

## v0.2.0 — 2026-07-15

Second Skills batch. Repo version bumped from 0.1.0 → 0.2.0 (new Skill added).

### Skills

| Skill | Version | Notes |
|---|---|---|
| `hlzd-inquiry-qualify` | 0.1.0 | No change (v0.1.0 from W1). 40 tests / 85% coverage. |
| `hlzd-b2b-research` | 0.1.0 | New. 4-step pipeline: HS lookup (hsbianma.com) + UN Comtrade + Google Trends + DDGS buyers + tender tracking. 31 tests for orchestrator + lib. Plus 4 standalone scripts (hs_lookup / trade_data / keyword_trends / buyer_search). |

### Architecture evolution

- Reusable `lib.py` introduced: shared logger, retry decorator, schema assertion, file cache
- `run_research.py` orchestrator unifies 4 step adapters with graceful degradation (missing deps → warnings, not crashes)
- All sub-scripts kept backward compatible (still runnable as standalone CLIs)
- Step functions designed for testability (mockable via `patch`)

### Verification

- `py validate_skills.py` → 2/2 OK (both Skill SKILL.md files conform to spec)
- `py -m pytest skills/hlzd-b2b-research/tests/` → 31/31 PASSED
- All 5 CLIs (4 sub-scripts + orchestrator) accept `--help` and report missing deps gracefully

---

## v0.1.0 — 2026-07-15

First public release.

### Skills

| Skill | Version | Notes |
|---|---|---|
| `hlzd-inquiry-qualify` | 0.1.0 | Initial release. 5-dim scoring (A/B/C/D), multi-language extraction, compliance coarse-screen, dual-use/red-flag detection, recommended-next-skill routing. 40 tests, 85% coverage. |

### Conventions established

- Repo metadata version follows semver (x: breaking, y: new skill, z: fixes)
- Skill metadata version bumps on any shipped change
- All scripts target Python 3.10+ with zero external deps (pydantic/pytest optional)
- CLI: `--input <file>` / `--stdin` dual channel, JSON to stdout
- SKILL.md ≤ 500 lines; details in `references/`
- `hlzd-` prefix required for all Skill names

### Roadmap (next 12 weeks)

See [docs/出海技能集规划.md](docs/出海技能集规划.md#七上线节奏12-周-roadmap)
