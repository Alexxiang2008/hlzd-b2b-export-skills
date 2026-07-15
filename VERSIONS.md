# VERSIONS

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
