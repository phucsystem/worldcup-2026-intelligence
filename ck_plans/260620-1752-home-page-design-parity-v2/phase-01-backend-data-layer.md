---
phase: 1
title: "Backend Data Layer"
status: pending
effort: "M"
---

# Phase 1: Backend Data Layer

## Overview

Deterministic foundation: persist the `intelligence` blob, add deterministic per-team scenario notes + tournament-summary math, and feed `fixture_id`s + candidate groups into `computed_facts` so the Phase-2 LLM stays grounded. No LLM or HTTP changes here.

## Requirements

- Functional: `articles.intelligence` column exists and round-trips JSON; `standings_math` exposes `group_scenarios()` (per-team notes) and `tournament_summary()`; collector facts carry `fixture_id`s for upcoming fixtures and candidate-group tables.
- Non-functional: pure functions stay pure + unit-tested; migration is reversible; no behavior change to existing brief output yet.

## Architecture

```
collector._build_facts(...)  ──>  computed_facts {
   ...existing...,
   upcoming_fixtures: [{fixture_id, home_team, away_team, kickoff_utc, group_name}],  # next ~3
   stake_groups: [ { group_name, rows:[{position, team, points, note, status}], ... } ] # contention groups
}

standings_math.group_scenarios(group_tables) -> per-group rows w/ deterministic `note` + `status`
standings_math.tournament_summary(matches, group_tables) -> {stage, matchday, matchday_total,
   teams_remaining, teams_total, days_to_next_phase, next_phase_label, group_stage_pct}
```

Per-team note derivation (deterministic, from `qualification_status` + position + max-possible points):
- `qualified` → note `"Through"`, css `qualified`
- `eliminated` → note `"Out"`, css `out`
- `contention` + position 1–2 → `"Win = top"` (css `contention`)
- `contention` + position 3–4 → `"Must win"` (css `contention`)

`tournament_summary` math:
- `stage` = "Group Stage" while any group incomplete, else "Knockout".
- `matchday`/`matchday_total` = max played across teams (cap 3) / 3 for group stage.
- `teams_remaining` = count teams not `eliminated`; `teams_total` = 48.
- `group_stage_pct` = finished group matches ÷ total scheduled group matches × 100.
- `days_to_next_phase` / `next_phase_label` = days from today (Australia/Melbourne) to earliest knockout (`group_name IS NULL`) kickoff; label e.g. "Round of 32". Null-safe when no knockout fixtures scheduled.

## Related Code Files

- Create: `backend/db/migrations/versions/0004_article_intelligence.py` (add nullable `intelligence` JSON column to `articles`; `down_revision="0003"`).
- Modify: `backend/app/data/repository.py` — add `sa.Column("intelligence", sa.JSON)` to `articles_table`; `upsert_article` writes `article.get("intelligence")` in both `.values()` and `on_conflict_do_update.set_`.
- Modify: `backend/app/data/standings_math.py` — add `group_scenarios()` + `tournament_summary()` (pure).
- Modify: `backend/app/pipeline/nodes_collector.py` — extend `_build_facts` with `upcoming_fixtures` (next ~3 by kickoff, score is None) and `stake_groups` (groups not fully decided, capped ~4); both must include `fixture_id` / `group_name` keys.
- Modify: `backend/app/pipeline/state.py` — no shape change needed (`computed_facts: dict`), but document new keys in a comment.
- Modify: `backend/tests/` — add `test_standings_scenarios.py` (or extend existing) for `group_scenarios` + `tournament_summary`.

## Implementation Steps

1. Write migration `0004_article_intelligence.py`: `op.add_column("articles", sa.Column("intelligence", sa.JSON(), nullable=True))`; `downgrade` drops it.
2. Add `intelligence` column to `articles_table` Core object in `repository.py` and persist it in `upsert_article` (values + conflict set). Default to `None` when absent so existing callers are unaffected.
3. Implement `standings_math.group_scenarios(group_tables)` returning, per group, ordered rows `{position, team, points, note, status}` using `qualification_status` + the note rules above. Reuse existing sort/`StandingRow` fields; do not recompute points.
4. Implement `standings_math.tournament_summary(matches, group_tables)` per the math above; keep timezone handling consistent with the codebase (Australia/Melbourne for the day delta).
5. Extend `nodes_collector._build_facts` to emit `upcoming_fixtures` (needs access to unplayed matches — query/keep alongside the existing match load) and `stake_groups` (call `group_scenarios`, keep only contention/incomplete groups, **cap 4**, ranked by soonest next fixture). <!-- Updated: Validation Session 1 - stake_groups cap fixed at 4 -->
   - `tournament_summary().days_to_next_phase` / `next_phase_label` return **`None`** when no knockout fixtures exist in the DB (group stage, knockout not yet seeded). Frontend hides that stat cell (Phase 3). <!-- Updated: Validation Session 1 - hide days-to-phase when null -->
6. Run `cd backend && pytest` (uses repo venv); add focused tests for the two new pure functions, including the incomplete-group and no-knockout edge cases.

## Success Criteria

- [ ] `alembic upgrade head` applies 0004; `downgrade -1` reverts cleanly.
- [ ] `upsert_article` persists and overwrites `intelligence` JSON (verified by a quick round-trip test or psql check).
- [ ] `group_scenarios` returns correct notes for qualified / eliminated / contention fixtures (unit-tested).
- [ ] `tournament_summary` returns correct figures for a complete vs incomplete group fixture set, and null-safe `days_to_next_phase` when no knockout fixtures (unit-tested).
- [ ] `computed_facts` includes `upcoming_fixtures` (with `fixture_id`) and `stake_groups`.
- [ ] `pytest` green.

## Risk Assessment

- **Best-thirds dependency:** `qualification_status` only computes best-thirds for 12-group format; local seed data may differ. Mitigation — `group_scenarios` consumes whatever status is returned; tests use representative tables, not live data.
- **Timezone drift** in `days_to_next_phase` → reuse the existing Australia/Melbourne convention; test with a fixed input date.
- **Migration/Core-object drift** — keep the `articles_table` Core object and migration in sync (the file comment already notes "Mirror migration schema").
