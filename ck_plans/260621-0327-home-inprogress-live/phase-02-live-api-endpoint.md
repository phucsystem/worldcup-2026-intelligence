---
phase: 2
title: Live API Endpoint
status: completed
effort: ''
---

# Phase 2: Live API Endpoint

## Overview

Expose live matches to the frontend via `GET /api/fixtures/live`, built on a pure `shape_live()` function tested alongside the existing shaping suite. Surface `elapsed` + `updated_at` on `FixtureRow` so the client can interpolate the minute.

Depends on Phase 1 (`elapsed` column + model field).

## Requirements

- Functional: `GET /api/fixtures/live` returns live matches, soonest-kicked first, each with `home/away_team`, logos, scores, `status`, `elapsed`, `group_name`, `kickoff_utc`, `updated_at`. Empty list when none live.
- Non-functional: DB read only (0 external calls); `/api/fixtures/upcoming` untouched; pure shaping unit-tested with no DB/network.

## Architecture

Live status set: `LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE"}` (in-play short codes; excludes NS and finished FT/AET/PEN). DB query selects matches whose `status` is in that set, ordered by `kickoff_utc`. `shape_live(rows, logos)` mirrors `shape_upcoming` style: enrich + sort soonest-kicked first. `FixtureRow` (both the API pydantic model in `fixtures.py` and the TS interface) gains `elapsed: Optional[int]` and `updated_at: Optional[datetime]`. `_enrich` and `_row_to_dict` carry the two new fields.

## Related Code Files

- Modify: `backend/app/api/fixtures.py` — add `LIVE_STATUSES`, `is_live_status()`, `shape_live()`, `LiveFixtures` response model (or reuse `list[FixtureRow]`), `GET /live` route; extend `FixtureRow` (+`elapsed`, +`updated_at`), `_enrich`, `_row_to_dict`.
- Modify: `backend/tests/test_fixtures_shaping.py` — tests for `is_live_status` + `shape_live`.

## Implementation Steps (TDD)

1. **Test first** — in `test_fixtures_shaping.py`, add `TestShapeLive`: feed mixed rows (`NS`, `2H` with elapsed, `FT`, `HT`) and assert `shape_live` returns only the `2H`+`HT` rows, soonest-kicked first, with `elapsed` preserved and `updated_at` passed through. Add `is_live_status` cases (`"2H"`→True, `"FT"`→False, `None`→False, case-insensitive if `shape_upcoming` precedent is case-sensitive — match existing convention, which is exact-match; keep exact codes). Update the `_match` test helper to accept `elapsed`/`updated_at`. Run → fails.
2. Add `LIVE_STATUSES`, `is_live_status(status)`, and `shape_live(rows, logos)` (sort key `(f.kickoff_utc is None, f.kickoff_utc)`, filter by `is_live_status`). Run → green.
3. Extend `FixtureRow` model with `elapsed: Optional[int] = None` and `updated_at: Optional[datetime] = None`; add both to `_enrich(...)` and `_row_to_dict(...)`.
4. Add the route:
   ```python
   @router.get("/live", response_model=list[FixtureRow])
   def get_live():
       session = _get_session()
       try:
           rows = session.execute(
               select(matches_table)
               .where(matches_table.c.status.in_(sorted(LIVE_STATUSES)))
               .order_by(matches_table.c.kickoff_utc)
           ).fetchall()
           logos = _logo_map(session)
       finally:
           session.close()
       return shape_live([_row_to_dict(r) for r in rows], logos).fixtures  # or return list directly
   ```
   (Decide: return bare `list[FixtureRow]` to keep the client simple — preferred. If a wrapper object is used, keep it consistent with `UpcomingFixtures`.)
5. Run full backend suite; manually hit `/api/fixtures/live` (expect `[]` with no live rows).

## Success Criteria

- [ ] `shape_live` + `is_live_status` unit tests pass; `_match` helper updated without breaking existing shaping tests.
- [ ] `GET /api/fixtures/live` returns `[]` when nothing live, and live rows soonest-first when present (verified with a temporary inserted row or via P3 seed).
- [ ] Response includes `elapsed` and `updated_at`.
- [ ] `/api/fixtures/upcoming` output unchanged.

## Risk Assessment

- **Response shape churn**: returning a bare list vs wrapper affects the frontend. Decide here (recommend bare `list[FixtureRow]`) and keep `api.ts` aligned in P4.
- **`updated_at` serialization**: ensure it serializes as ISO-8601 so the client `Date.parse` works; FastAPI/pydantic does this for `datetime` by default.
