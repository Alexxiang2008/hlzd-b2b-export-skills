# Methodology Reference

Detailed methodology for the `b2b-overseas-market-report` skill. Load this when synthesizing a complex report or when you need to verify the report's methodology is correctly cited.

## 5-Step Output Process

```
Step 0.45  Query Quality Pre-Flight       (~5s)
Step 0.55  Pre-Research (Brave Search)    (~10s)
Step 0.75  Plan Generation                (~3s)
Step 1     last30days Engine              (1-3 min, 152s typical)
Step 2     Supplement Search (Brave)      (~30s)
Step 2.5   Append WebSearch to raw file   (~3s)
Synthesis Me (handcrafted transform)      (~10 min)
─────────────────────────────────────────────
Total: ~15 min wall clock
```

### Step 0.45 — Query Quality Pre-Flight

Reject the query if it matches any of these 4 keyword-trap classes:

- **Class 1: Demographic shopping** — `gift for {age} {gender}`, `present for {demographic}`
- **Class 2: Numeric trap** — `42 year old man` (collides with jersey #42, Hitchhiker's)
- **Class 3: Overly-literal concept** — `how to use X` (people don't post that way on Reddit)
- **Class 4: Generic single-noun** — `sneakers`, `headphones` (no anchor)

If the query matches, ask ONE clarifying question. Do NOT run the engine.

### Step 0.55 — Pre-Research

Use Brave Search (via `supplement_search.py`) to find:

- Active subreddits for the topic
- 2026 review stations (TechCrunch, PCMag, niche blogs)
- Current events context for subquery generation

**Fallback chain**:
- If `WebSearch` MCP tool returns 400 → use `supplement_search.py`
- If `WebFetch` is blocked by enterprise policy → use `supplement_search.py` exclusively
- If both fail → run engine with whatever signal is available, accept thinner data

### Step 0.75 — Plan Generation

Generate a JSON query plan with 3 subqueries:

```json
{
  "intent": "factual",
  "freshness_mode": "balanced_recent",
  "cluster_mode": "story",
  "subqueries": [
    {
      "label": "primary_pain_points",
      "search_query": "[topic] pain points",
      "ranking_query": "What are the most common complaints?",
      "sources": ["reddit", "youtube", "tiktok", "instagram", "hackernews", "grounding"],
      "weight": 1.0
    },
    {
      "label": "feature_requests",
      "search_query": "[topic] features wanted 2026",
      "weight": 0.8
    },
    {
      "label": "competitive_2026",
      "search_query": "[brand A] vs [brand B] vs [brand C] 2026",
      "weight": 0.6
    }
  ]
}
```

Save to `/tmp/last30days-plan-XXXXXX` and pass via `--plan "$FILE"`.

### Step 1 — Run Engine

```bash
"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/last30days.py" "[TOPIC]" \
  --emit=compact --save-dir="${LAST30DAYS_MEMORY_DIR}" --save-suffix=v3 \
  --plan "$PLAN_FILE" \
  --subreddits="sub1,sub2,sub3,..." \
  --tiktok-hashtags="tag1,tag2,..." \
  --x-handle="handle"
```

5-min timeout. The engine produces ~50-100 items in 152s typical.

### Step 2 — Supplement Search

```bash
python ~/.config/last30days/scripts/supplement_search.py \
  "review 2026 best [topic]" \
  "[brand A] vs [brand B] 2026" \
  "[topic] pain points reddit"
```

3 queries × 5 results = 15 new 2026-dated data points. Save outputs to append to raw file.

### Step 2.5 — Append to Saved Raw File

```bash
RAW_FILE="${LAST30DAYS_MEMORY_DIR}/[slug]-raw-v3.md"
cat >> "$RAW_FILE" << 'EOF'

## WebSearch Supplemental Results

- **Station A** (domain.com) — 1-2 sentence excerpt of what you found
- **Station B** (other.com) — 1-2 sentence excerpt
- ...
EOF
```

Each bullet: `- **{Publisher}** ({domain}) — {excerpt}`. No URLs (domain in parens is the citation).

### Synthesis — Handcrafted Transform

Read the engine output + supplement_search.py results. Transform into:

1. **TL;DR card** with 3 active trends (NOT "best window" claims)
2. **5-row conclusion table** (conclusion + business meaning)
3. **3 core signals** with user-quote + blockquote + business implication
4. **4 platform deep dives** with stats + 5 findings each
5. **Strategic comparison table** (3+ vendors × 10 dimensions)
6. **3-step action plan** in green action cards
7. **Methodology & limitations** section (transparent self-audit)

## 5-Dimension Signal Judgment (ad-hoc heuristic)

A finding is a "real signal" if it scores on most of these 5 dimensions:

| Dimension | Question to ask |
|---|---|
| **30-day activity** | Does it have engagement numbers (upvotes > 10, views > 1K) in the last 30 days? |
| **Cross-source consensus** | Does the same signal appear in ≥ 2 independent sources? |
| **Time freshness** | Is the source dated 2026-07 or later? (Not 2024 / 2025 cached) |
| **Engagement strength** | Composite of upvotes + likes + views (weighted by source) |
| **Cross-platform** | Does the same trend surface in ≥ 3 platforms (Reddit + YouTube + Web)? |

**Heuristic, not rigorous framework**. State this in the Methodology section of every report.

## 7 Limitations to Disclose (yellow callout)

Every report MUST include a yellow-box disclosure of these 7 things the report does NOT have:

1. **No market size data** — never accessed IHS Markit, Statista, Parks Associates
2. **No historical comparison** — 30-day window, can't say "2024 was better"
3. **No sales data** — only social signals, not actual transactions
4. **No PESTEL framework** — political / tariff / regulatory dimensions missing
5. **No expert interview** — pure social listening
6. **No statistical significance** — small sample, not statistically representative
7. **No competitor financial data** — no GMV / margin / cash flow

Plus a "how to use this report" statement: **starting point heuristic, not investment decision basis**.

## Soft Language Dictionary

Use these instead of dogmatic claims:

| ❌ Avoid | ✅ Use instead |
|---|---|
| "2026 is the best window" | "30-day signal shows active trends" |
| "Chinese sellers are absent" | "No Chinese sellers surfaced in the 30-day signal" |
| "Reolink is winning the market" | "Reolink was the most-mentioned brand in 3+ sources" |
| "The market is $X billion" | "No market size data available; see Limitations" |
| "This proves X" | "30-day data shows X is a real signal (see Methodology)" |
| "Reolink is the best for OEM" | "Reolink route is one option for B2B exporter — see Risks" |

## Quality Control Checklist (before saving the HTML)

- [ ] Methodology section explicitly states "ad-hoc heuristic, not rigorous framework"
- [ ] Limitations section lists all 7 items
- [ ] All signal judgment uses soft language (no "best window" / "winning" / "proves")
- [ ] Audience is "B2B cross-border business leads", not the user's specific company
- [ ] Brand names appear only as authoring organization in footer, not as audience assumption
- [ ] Every claim is grounded in a real engagement signal (upvotes, views, likes) or 2026 URL
- [ ] No em-dashes (`—`) or en-dashes (`–`) in body text
- [ ] No trailing `Sources:` block (footer table is the citation)
- [ ] All citations are inline `[name](url)` markdown links
- [ ] Engine stdout noise stripped via `scripts/extract_html_noise.py`
- [ ] All 9 sections present in correct order
- [ ] Cover has L1 (action) / L2 (data) / L3 (meta) visual hierarchy

## Common Failure Modes

| Failure | Recovery |
|---|---|
| User query has no signal in any platform | Reframe: ask user for more specific sub-category |
| WebSearch / WebFetch both blocked | Use only `supplement_search.py` + engine, accept thinner data |
| yt-dlp transcripts all fail (EJS wall) | Engine emits EJS-flavored nudge; user adds `--remote-components ejs:github` to `yt-dlp.conf` |
| Engine returns < 5 items per source | Switch to `--deep` mode (1-3 min longer runtime) |
| YouTube 0/10 transcripts on non-news topic | Captions don't exist on those videos; quality_nudge skips degraded flag — no action needed |
| Plan C EJS-aware nudge didn't trigger | Confirm `youtube_videos_count > 0`; if 0, degraded check is skipped by design |
