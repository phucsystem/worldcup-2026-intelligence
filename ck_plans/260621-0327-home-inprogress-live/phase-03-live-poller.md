---
phase: 3
title: Live Poller
status: completed
effort: ''
---

# Phase 3: Live Poller

## Overview

A lightweight, window-gated background loop that refreshes live scores/minute by polling `?live=all` every 120s — but only while a match is actually in its window — and upserts just score/status/elapsed/`updated_at`. Never runs standings or the LLM. Includes a seed helper so the feature is demoable without a paid plan.

Depends on Phase 1 (`get_fixtures(live=True)`, `elapsed`).

## Requirements

- Functional: `collect_live()` fetches live fixtures and upserts only their match rows. `live_poller.py` runs forever: when ≥1 stored fixture is in `[kickoff, kickoff+LIVE_WINDOW]`, poll every `LIVE_POLL_SECONDS` (120); else sleep `IDLE_SLEEP_SECONDS` (e.g. 300) and re-check. Window detection is a pure, unit-tested function.
- Non-functional: no LLM, no standings recompute, no prune; zero external requests when no window is active; safe to run as its own process/container.

## Architecture

- `should_poll_now(fixtures, now, window=timedelta(hours=3)) -> bool` — pure: True if any fixture has `kickoff <= now <= kickoff + window`. Unit-testable with fixed datetimes.
- `collect_live(session_factory, client)` — `client.get_fixtures(live=True)` → `upsert_matches(session, live_matches)` (reuses Phase 1 upsert; `elapsed`/scores/status flow through). No `prune_matches_not_in`, no standings, no teams.
- `live_poller.main()` — build client + session factory once; loop: read upcoming/in-window fixtures from DB (cheap query on `kickoff_utc`), `should_poll_now` → either `collect_live` + sleep 120 or sleep 300. Guard on `API_FOOTBALL_KEY` like `collect.run`.
- Config: add `LIVE_POLL_SECONDS=120`, `IDLE_SLEEP_SECONDS=300`, `LIVE_WINDOW_HOURS=3` to `config.py` (env-overridable).

## Related Code Files

- Create: `backend/app/pipeline/live_poller.py` (entrypoint loop; mirrors `scheduler_entry.py` structure)
- Modify: `backend/app/data/collect.py` — add `collect_live(...)` (or place in a new `backend/app/data/collect_live.py` if `collect.py` grows unwieldy)
- Modify: `backend/app/config.py` — poll/window settings
- Create: `backend/scripts/seed_live_match.py` (or a `seed_openfootball.py`-style helper) — insert/flip one stored match to a live status with `elapsed` for demo
- Modify: `docker-compose.yml` — add a `live_poller` service running `python -m app.pipeline.live_poller` (note for `260621-azure-vm-deploy`)
- Modify: `backend/tests/` — `test_live_poller.py` for `should_poll_now`

## Implementation Steps (TDD)

1. **Test first** — `test_live_poller.py::test_should_poll_now`: fixture kicked off 30 min ago ⇒ True; kicks off in 2h ⇒ False; kicked off 4h ago (past window) ⇒ False; empty list ⇒ False. Run → fails (function absent).
2. Implement `should_poll_now` (pure). Run → green.
3. Implement `collect_live(session_factory, client)`: fetch `client.get_fixtures(live=True)`; if any returned, `upsert_matches`. Log count. Keep it dependency-light so it can be unit-tested with a fake client + in-memory/session stub (optional integration test; at minimum assert it calls upsert with the live matches via a fake).
4. Implement `live_poller.main()` loop with the config-driven intervals and the `API_FOOTBALL_KEY` guard. Keep the in-window DB query minimal (select fixtures with `kickoff_utc` not null within a coarse range, or all and let `should_poll_now` decide).
5. Add config settings with safe defaults.
6. Write `seed_live_match.py`: set one existing match (or insert a synthetic one) to `status="2H"`, `home_score`/`away_score`, `elapsed=67`, `updated_at=now`. Used to demo P4 without a paid plan.
7. Add the `live_poller` compose service. Document that the deploy plan (`260621-azure-vm-deploy`) must include it.
8. Run backend suite; manually run the poller once with a seeded window to confirm it upserts and otherwise idles.

## Success Criteria

- [ ] `should_poll_now` unit tests pass (in-window / future / past / empty).
- [ ] `collect_live` upserts only live matches; never calls standings/prune/LLM (assert via fake client or code review + test).
- [ ] Poller idles (no API calls) when no fixture is in window; polls at 120s when one is.
- [ ] `seed_live_match.py` produces a row that makes `/api/fixtures/live` return one match.
- [ ] `live_poller` compose service starts and loops without crashing.

## Risk Assessment

- **`?live=all` cross-league results** (from P1): filter `collect_live` to fixtures we already store (`fixture_id` in DB) so foreign live games don't pollute `matches`.
- **Hot loop / crash loop**: ensure exceptions in a poll are caught + logged and the loop sleeps before retry (don't spin on API errors / quota-exhausted responses, which raise `RuntimeError`).
- **Runtime model**: this is a long-running loop, not the cron `scheduler_entry`. Must be its own process/container; do not fold into the daily-brief job.
