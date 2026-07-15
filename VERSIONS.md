# VERSIONS

## v0.6.0 — 2026-07-15

Sixth Skills batch. Repo version bumped 0.4.0 → 0.6.0 (2 new Skills added). End-to-end closed loop achieved.

### Skills

| Skill | Version | Notes |
|---|---|---|
| `hlzd-inquiry-qualify` | 0.1.0 | No change. 40 tests. |
| `hlzd-b2b-research` | 0.1.0 | No change. 31 tests. |
| `hlzd-buyer-finder` | 0.1.0 | No change. 45 tests. |
| `hlzd-market-report` | 0.1.0 | No change. 41 tests. |
| `hlzd-customer-due-diligence` | 0.1.0 | NEW. 5-dim scoring (real-company / size / customer-type / procurement / risk) + OFAC SDN static 20-name subset + sanctioned-country + dual-use + fraud coarse-screen. 57 tests. Auto-routes to hlzd-cold-outreach or hlzd-trade-compliance. |
| `hlzd-cold-outreach` | 0.1.0 | NEW. 6 buyer-type templates (Manufacturer / EPC / Distributor / OEM / End User / Trader) x 2 languages (en/es). Variable substitution + Day 7/Day 14 followup sequence. 35 tests. |

### Closed-loop B2B export pipeline

First end-to-end working chain:

```
hlzd-b2b-research      →  HS + market size + trends
hlzd-buyer-finder      →  importers list
hlzd-customer-due-...  →  grade A/B → halt route to compliance
hlzd-cold-outreach     →  email drafts + followup
```

W4-5 (touch outreach layer) milestone complete: 2 of 3 Skills shipped; followup-sequencer deferred to v0.6.1.

### Architecture evolution

- **OFAC SDN static subset pattern** — v0.1 hardcodes 20 high-priority entity names; upgrade path to OFAC SDN API noted in SKILL.md
- **Variable preservation rule** — fill_template leaves unknown `{{var}}` as-is + tracks in `missing_variables[]` for human review (no silent defaults)
- **Word-limit advisory** — `within_word_limit` field is non-blocking; human review flag, not hard fail
- **Multi-language strategy** — v0.1 es (Latin America / Spain); ar / zh / ru / pt planned v0.2

### Verification

- `py validate_skills.py` → 6/6 OK
- Per-skill pytest (cumulative):
  - `hlzd-inquiry-qualify`: 40/40
  - `hlzd-b2b-research`: 31/31
  - `hlzd-buyer-finder`: 45/45
  - `hlzd-market-report`: 41/41
  - `hlzd-customer-due-diligence`: 57/57
  - `hlzd-cold-outreach`: 35/35
- **Cumulative across all 6 Skills: 249 tests PASSED**

---

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
