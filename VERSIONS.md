# VERSIONS

## v0.10.0 — 2026-07-16

Eighth Skills batch. Added `hlzd-product-image-gen` (slot 10/21): B2B 工业品产品图（T2I/I2I/抠图/阿里国际站主图）生成，Agnes Image 2.1 Flash + rembg。

### Skill added

| Skill | Version | Notes |
|---|---|---|
| `hlzd-product-image-gen` | 0.1.0 | NEW. B2B 工业品产品图（T2I/I2I/抠图/阿里国际站主图）生成，Agnes Image 2.1 Flash + rembg。 |

### Verification

- `py validate_skills.py` → OK
- `py -m pytest skills/hlzd-product-image-gen/tests/` → see PR

---

## v0.9.0 — 2026-07-16

Quotation engine ships: 3 new Skills (solution-match / quotation-gen / negotiation-playbook).
Repo version bumped 0.6.0 → 0.9.0 (3 new Skills added).

### Skills

| Skill | Version | Notes |
|---|---|---|
| `hlzd-inquiry-qualify` | 0.1.0 | No change. 40 tests. |
| `hlzd-b2b-research` | 0.1.0 | No change. 31 tests. |
| `hlzd-buyer-finder` | 0.1.0 | No change. 45 tests. |
| `hlzd-market-report` | 0.1.0 | No change. 41 tests. |
| `hlzd-customer-due-diligence` | 0.1.0 | No change. 57 tests. |
| `hlzd-cold-outreach` | 0.1.0 | No change. 35 tests. |
| `hlzd-solution-match` | 0.1.0 | NEW. 5-dim SKU matching (spec / qty / lead / price-tier / risk) + 3 plans (best/alt/cost-effective). Hardcoded 5-SKU catalog with OCTG / Solar / Steel. 31 tests. |
| `hlzd-quotation-gen` | 0.1.0 | NEW. FOB / CIF / DDP 3 incoterm calc + profit health (HEALTHY / BELOW_HEALTHY / LOW / HIGH) + payment terms suggestion. Static FX + region freight + customs duty 6% stub. 28 tests. |
| `hlzd-negotiation-playbook` | 0.1.0 | NEW. 3-round concession path × 3 axes (price / lead / payment) + breach detection + decision matrix (accept_round_2 / counter / counter_with_freight / walk_away / accept_round_3). 28 tests. |

### Closed-loop B2B export pipeline

End-to-end chain now spans 9 Skills:

```
research (b2b-research)
  -> buyers (buyer-finder)
  -> diligence (customer-due-diligence)
  -> outreach (cold-outreach)
  -> solution (solution-match)
  -> quote (quotation-gen)
  -> negotiate (negotiation-playbook)
```

W6-7 milestone complete: 3 of 3 Skills shipped (solution-match / quotation-gen / negotiation-playbook).

### Architecture evolution

- **Catalog + cost model** — solution-match ships with 5-SKU hardcoded catalog; quotation-gen ships with static FX rate dict + region-based freight heuristic + 6% customs duty stub. Both have v0.2 upgrade paths to ERP / FX API / real customs table.
- **Profit health bands** — quotation-gen uses 4-tier health (HEALTHY 15-25% / LOW <10% / BELOW_HEALTHY 10-15% / HIGH >25%) with explicit `warning` text per band.
- **Concession table** — negotiation-playbook defaults to 5% / 3% / 2% price, 0d / 5d / 10d lead, 30/70 -> 20/80 -> 10/90 payment. CLI --redline-price / --redline-lead overrides.
- **Decision matrix** — automatic routing based on (price_breach, lead_breach, competitor_risk) tuple.

### Verification

- `py validate_skills.py` → 9/9 OK
- Per-skill pytest (cumulative):
  - `hlzd-inquiry-qualify`: 40/40
  - `hlzd-b2b-research`: 31/31
  - `hlzd-buyer-finder`: 45/45
  - `hlzd-market-report`: 41/41
  - `hlzd-customer-due-diligence`: 57/57
  - `hlzd-cold-outreach`: 35/35
  - `hlzd-solution-match`: 31/31
  - `hlzd-quotation-gen`: 28/28
  - `hlzd-negotiation-playbook`: 28/28
- **Cumulative across all 9 Skills: 336 tests PASSED**

---

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

## v1.0.0 — 2026-07-16

First major version. Repo bumped 0.9.0 → 1.0.0 (W8 compliance shield ships; project crosses 10 Skill milestone).

### Skills

| Skill | Version | Notes |
|---|---|---|
|  | 0.1.0 | No change. 40 tests. |
|  | 0.1.0 | No change. 31 tests. |
|  | 0.1.0 | No change. 45 tests. |
|  | 0.1.0 | No change. 41 tests. |
|  | 0.1.0 | No change. 57 tests. |
|  | 0.1.0 | No change. 35 tests. |
|  | 0.1.0 | No change. 31 tests. |
|  | 0.1.0 | No change. 28 tests. |
|  | 0.1.0 | No change. 28 tests. |
|  | 0.1.0 | NEW. 5 sanit-y checks (4 buyer-side: OFAC SDN / EU Consolidated / BIS Entity / Country-Based Embargo, plus 1 product-side: ECCN dual-use) -> CLEARED / PENDING_REVIEW / BLOCKED clearance with audit_trail. Static subsets (33 OFAC + 17 EU + 15 BIS = 65 rows). 4-tier fuzzy matching (exact / bidirectional substring / long-token share / stopword-filtered). 48 tests, 85% lib/sources coverage. |

### v1.0 milestone

- 10/10 Skills pass 
- 384/384 tests pass (W8 adds 48)
- Repo metadata version  (semver major because compliance is production-critical)
- W2-3 / W4-5 / W6-7 / W8 milestones all complete
- Roadmap now starts at W9 (CI / 4-channel install / seed-customer demo / GitHub publish)

### v0.2 upgrade notes (planned for trade-compliance)

- Plug in live OFAC SDN CSV via Treasury API (1.5 万 entries)
- Plug in EU CFSP RSS feed for real-time Consolidated updates
- Plug in BIS Entity List + Denied Persons List via commerce.gov CSV
- Auto-classify HS code against ECCN (full CCL mapping)
- Real time OFAC 50% rule check (secondary sanctions)

