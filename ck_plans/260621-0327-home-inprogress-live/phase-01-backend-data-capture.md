---
phase: 1
title: Backend Data Capture
status: completed
effort: ''
---

# Phase 1: Backend Data Capture

## Overview

Capture the live match minute (`elapsed`) end-to-end: persist it on `matches`, map it from the API-Football payload, and let the client request only in-play fixtures via `?live=all`. This unblocks both the endpoint (P2) and the poller (P3).

## Requirements

- Functional: `matches` rows carry an integer `elapsed` (nullable); `_map_fixture` populates `Match.elapsed` from `fixture.status.elapsed`; `APIFootballClient.get_fixtures(live=True)` issues `?live=all`.
- Non-functional: existing collect/upsert paths keep working (`elapsed` defaults to `None`); migration is reversible; no change to `/api/fixtures/upcoming` behavior.

## Architecture

`fixture.status.elapsed` (int or null) → `_map_fixture` → `Match.elapsed` → `upsert_matches` → `matches.elapsed`. `get_fixtures(live=True)` adds `live=all` to params (mutually exclusive with the date window in practice; `live=all` ignores league/season filtering server-side but those params are harmless to keep).

## Related Code Files

- Create: `backend/db/migrations/versions/0005_match_elapsed.py`
- Modify: `backend/app/data/models.py` (add `Match.elapsed: Optional[int] = None`)
- Modify: `backend/app/data/api_football.py` (`_map_fixture` reads `status_obj.get("elapsed")`; `get_fixtures(live: bool = False)`)
- Modify: `backend/app/data/repository.py` (`upsert_matches` writes `elapsed` on insert + update)
- Modify: `backend/tests/test_fixtures_shaping.py` (or a new `backend/tests/test_api_football_mapping.py` if mapping tests don't belong with shaping)

## Implementation Steps (TDD)

1. **Test first** — add a mapping test: a raw fixture dict with `fixture.status = {"short": "2H", "elapsed": 67}` and goals `1/0` ⇒ `_map_fixture` returns `Match` with `elapsed == 67`, `home_score == 1`, `status == "2H"`. Add a second case: `status.elapsed` absent / `null` ⇒ `elapsed is None`. Run; assert it fails (no `elapsed` field yet).
2. Add `elapsed: Optional[int] = None` to `Match` (`models.py`).
3. In `_map_fixture`, set `elapsed=status_obj.get("elapsed")` (already have `status_obj`). Keep it `None` when not in play is acceptable — API returns null for NS anyway. Run mapping test → green.
4. **Test first** — add a `get_fixtures` param test using a stub/mock of `_get` (or assert on params passed): `get_fixtures(live=True)` includes `"live": "all"`; default call does not. If `_get` is awkward to intercept, extract param-building or assert via monkeypatched `httpx`. Keep it a true unit test (no network).
5. Implement `get_fixtures(self, date_from=None, date_to=None, live: bool = False)`: when `live`, set `params["live"] = "all"`. Run → green.
6. Write migration `0005_match_elapsed.py` (`down_revision = "0004"`): `op.add_column("matches", sa.Column("elapsed", sa.Integer(), nullable=True))`; downgrade drops it. Match the style of `0004_article_intelligence.py`.
7. Extend `upsert_matches` to set `elapsed=m.elapsed` in both `.values(...)` and `on_conflict_do_update` `set_={...}`.
8. Apply migration locally (`alembic upgrade head` per repo convention) and run the full backend test suite.

## Success Criteria

- [ ] New mapping tests for `elapsed` (present + absent) pass; pre-existing tests still pass.
- [ ] `get_fixtures(live=True)` unit test asserts `live=all` is sent; default omits it.
- [ ] `0005` migration applies and reverses cleanly; `matches.elapsed` exists, nullable.
- [ ] `upsert_matches` persists `elapsed` on insert and update.
- [ ] `/api/fixtures/upcoming` response is unchanged (regression check).

## Risk Assessment

- **`?live=all` + league/season params**: API-Football may ignore league filter under `live=all`, returning other leagues' live games. Mitigation: P2/P3 filter to known fixture_ids / our stored matches, and the WC league id scoping is re-applied when shaping. Note for P3.
- **Migration ordering**: confirm `0004` is current head before authoring `0005`.
