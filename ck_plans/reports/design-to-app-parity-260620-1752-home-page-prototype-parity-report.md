# Brainstorm Report — Home Page Prototype → App Parity

- **Date:** 2026-06-20
- **Topic:** Align production app home page (`frontend/app/page.tsx`) to the updated design (`prototypes/s01-brief-list.html`)
- **Decisions:** Full parity · LLM-generated stakes via brief pipeline · Hybrid scenario notes · Keep Stars + Earlier
- **Modes:** none (`--html`/`--wiki` not requested)

## Problem statement

Prototype `s01-brief-list.html` has 650 lines of uncommitted design changes that put it ahead of the live app. Five new/enhanced sections exist in the design with no implementation. Goal: bring the app to full visual + functional parity, sourcing the editorial content the API doesn't yet produce.

## Gap analysis (prototype → app)

| Design section | App today | Data source |
|---|---|---|
| Summary panel (stage, matchday, teams remaining, days-to-R32, group-stage %) | none | Derivable (no field today) |
| Up next — rich `next-match` card + fixture list w/ stakes | plain single `FixtureRow` | fixtures exist / **stake text editorial** |
| Today's brief hero + result chips | done | done |
| Latest Results widget (grouped + "Display in Groups" toggle) | flat `ResultChips` only | `standings.recent_results` |
| What's at stake stake-cards (mini tables + scenario notes) | none | table data exists / **scenario notes + line editorial** |

**Reverse gap:** app has *Stars to watch* + *Earlier briefs* that the new prototype dropped → **decision: keep both** (design becomes a superset).

**Styling note:** app already reuses prototype class names, but `globals.css` carries only ~11 of the 50+ classes. New CSS ports directly.

## Pipeline context

Brief flow: **collector → analyst (`Intelligence` pydantic, DeepSeek) → editor (article)** → `articles_table` → `/api/briefs`. `intelligence` is currently computed then dropped. Natural home for stakes.

## Evaluated approaches (scenario-note sourcing)

- **A — All LLM:** notes + lines + stakes in one call. Simplest; hallucination risk on structured qualification logic.
- **B — Hybrid (CHOSEN):** `standings_math` computes deterministic per-team notes; LLM writes only narrative line + fixture stakes. Best accuracy/cost, reuses existing math.
- **C — Separate stakes endpoint + own LLM call:** most flexible refresh; extra cost + second integration. Rejected (YAGNI).

## Recommended solution

**Backend**
1. Extend analyst `Intelligence` model + prompt: `fixture_stakes: [{fixture_id, stake_text}]` (keyed to real `fixture_id`s passed into `computed_facts`) and `group_scenarios: [{group_name, tag, line}]`. Per-team notes computed by `standings_math`, not LLM.
2. Persist `intelligence` (new nullable JSON column on `articles_table`) and expose one new field on `BriefDetail`.
3. Tournament summary: deterministic compute via `standings_math` → `{stage, matchday x/3, teams_remaining x/48, days_to_next_phase, group_stage_pct}`.

**Frontend**
4. Port new CSS classes `prototypes/components.css` → `globals.css`.
5. New components: `SummaryPanel`, rich `NextMatchCard`, `FixtureListItem` (w/ stake), `ResultsWidget` (`"use client"`, toggle ported from `interactions.js`), `StakeGrid`/`StakeCard`.
6. Rewire `page.tsx` order: Summary → Up next (card + fixture list + See-all) → Today's brief → Latest Results → What's at stake → Stars (kept) → Earlier (kept).
7. Wire data: results widget ← `standings.recent_results`; stakes/scenarios ← brief `intelligence`; summary ← new compute.

## Risks & mitigations

- **LLM hallucination** → key stakes to real `fixture_id`s; per-team notes deterministic (option B).
- **Freshness** → stakes only as fresh as last daily brief run; acceptable for daily-brief product.
- **Server/client boundary** → only `ResultsWidget` is `"use client"`; rest stay server components.
- **DeepSeek structured-output token/cost increase** → minor; monitor.

## Success criteria

- Home page renders all five sections matching the prototype layout/visuals.
- Fixture stakes + group scenario lines populate from the latest brief; per-team notes match `standings_math` qualification logic.
- Summary panel figures are correct against current fixtures/standings.
- Stars + Earlier sections retained.
- Graceful degrade when brief/intelligence absent (sections hide, no crash).

## Open questions

- Endpoint shape for tournament summary: dedicated `/api/tournament/summary` vs. folding into `/api/standings` or `/api/fixtures/upcoming` — to settle in planning.
- Backfill: persist `intelligence` only for new briefs, or backfill latest? (Likely new-only; latest brief re-runs daily.)
