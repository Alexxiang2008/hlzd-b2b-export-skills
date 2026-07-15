# VERSIONS

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
