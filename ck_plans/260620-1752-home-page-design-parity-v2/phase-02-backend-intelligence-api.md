---
phase: 2
title: "Backend Intelligence & API"
status: pending
effort: "M"
dependencies: [1]
---

# Phase 2: Backend Intelligence & API

## Overview

Make the LLM emit grounded stakes + group narrative, persist the full `intelligence` blob through the pipeline, and expose `intelligence` + a new tournament-summary endpoint over HTTP. Per-team notes come from Phase-1 math, merged with the LLM line/tag by `group_name`.

## Requirements

- Functional: analyst returns `fixture_stakes` (keyed to real `fixture_id`s) + `group_scenarios` (`{group_name, tag, line}`); pipeline persists `intelligence`; `GET /api/briefs/latest` & `/{date}` expose `intelligence`; `GET /api/tournament/summary` returns the summary.
- Non-functional: LLM stays grounded (uses only provided `fixture_id`s/groups); existing article output unchanged; new fields nullable/optional for graceful degrade.

## Architecture

```
analyst_node:
  Intelligence (extended) {
    ...existing 5 fields...,
    fixture_stakes: list[FixtureStake]   # {fixture_id:int, stake_text:str}
    group_scenarios: list[GroupScenario] # {group_name:str, tag:str, line:str}
  }
  -> state["intelligence"] = intelligence.model_dump()

run_pipeline persist:
  upsert_article(session, {**article, "intelligence": merged_intelligence}, ...)
  merged_intelligence = intelligence + per-team notes from facts["stake_groups"]
  (merge group_scenarios[].line/tag with stake_groups[].rows by group_name)

API:
  BriefDetail += intelligence: dict | None
  GET /api/tournament/summary -> TournamentSummary (calls Phase-1 tournament_summary over current DB)
```

Grounding: `ANALYST_USER` already passes `facts_json`. Phase-1 added `upcoming_fixtures` (with `fixture_id`) and `stake_groups` to facts. Extend the prompt to instruct: emit one `fixture_stakes` entry per provided `upcoming_fixtures.fixture_id` (echo the id, never invent), and one `group_scenarios` entry per provided `stake_groups.group_name` (tag = short status like "Decided tonight"/"Tomorrow"; line = one-sentence narrative citing provided facts). Keep the existing "do not compute numbers" rules.

## Related Code Files

- Modify: `backend/app/pipeline/nodes_analyst.py` — extend `Intelligence` with `FixtureStake` + `GroupScenario` submodels (lists default `[]`).
- Modify: `backend/app/pipeline/prompts.py` — extend `ANALYST_USER` with the two new output fields + grounding rules.
- Modify: `backend/app/pipeline/run.py` — after editor node, merge per-team notes from `computed_facts["stake_groups"]` into the intelligence dict and pass it to `upsert_article`.
- Modify: `backend/app/data/repository.py` — `upsert_article` already persists `intelligence` (Phase 1); ensure `run.py` passes it.
- Modify: `backend/app/api/briefs.py` — add `intelligence: dict | None` to `BriefDetail`; populate in `_to_detail`.
- Create: `backend/app/api/tournament.py` — `GET /api/tournament/summary` router calling `tournament_summary()` over current matches/standings.
- Modify: `backend/app/main.py` — register the tournament router.
- Modify: `backend/tests/` — analyst structured-output shape test (mock client) + tournament endpoint test.

## Implementation Steps

1. Add `FixtureStake(BaseModel){fixture_id:int, stake_text:str}` and `GroupScenario(BaseModel){group_name:str, tag:str, line:str}` to `nodes_analyst.py`; add `fixture_stakes: list[FixtureStake] = []` and `group_scenarios: list[GroupScenario] = []` to `Intelligence`. (Defaults keep the structured client tolerant.)
2. Extend `ANALYST_USER` in `prompts.py` with the two new fields + grounding instructions (echo provided `fixture_id`s; one scenario per provided group; cite facts; no invented numbers).
3. In `run.py`, build `merged_intelligence`: take `state["intelligence"]`, attach per-team note rows from `computed_facts["stake_groups"]` keyed by `group_name` (so `group_scenarios` carries both LLM `line/tag` and deterministic `rows`). Pass `{**article, "intelligence": merged_intelligence}` to `upsert_article`.
4. Add `intelligence` to `BriefDetail` (briefs.py) and read `row.intelligence` in `_to_detail`. Keep nullable.
5. Create `tournament.py` router: load matches + group tables (reuse collector/standings helpers or query directly), call `tournament_summary()`, return a `TournamentSummary` pydantic response. Register in `main.py`.
6. Tests: assert analyst returns the new fields with a mocked structured client; assert `/api/tournament/summary` returns expected keys; run `cd backend && pytest`.

## Success Criteria

- [ ] `Intelligence.model_dump()` includes `fixture_stakes` + `group_scenarios`.
- [ ] A pipeline run persists a non-null `articles.intelligence` containing stakes + scenarios (LLM line/tag) + deterministic per-team note rows merged by group.
- [ ] `GET /api/briefs/latest` returns `intelligence`; absent → `null`, not an error.
- [ ] `GET /api/tournament/summary` returns `{stage, matchday, matchday_total, teams_remaining, teams_total, days_to_next_phase, next_phase_label, group_stage_pct}`.
- [ ] No regression in existing `title/summary/body_md` output.
- [ ] `pytest` green.

## Risk Assessment

- **LLM ignores fixture_id grounding / hallucinates groups** → frontend (Phase 4) matches stakes by `fixture_id` and renders only groups present in both LLM output and deterministic rows; unmatched entries are dropped, not shown.
- **Token/cost increase** from larger structured output → minor; monitor `agent_runs.cost_usd`.
- **Structured-client schema strictness** → defaulting the new lists to `[]` avoids parse failures on older/sparse responses.
- **Partial failure** (analyst succeeds, editor fails) → existing retry/error path in `run.py` unchanged; intelligence merge guarded against missing keys.
