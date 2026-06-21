# Brainstorm — In-Progress (Live) Section, Home Page

- **Date:** 2026-06-21
- **Topic:** Implement the in-progress/live match section on the production home page (Next.js app), backing the `.is-live` prototype variant with real data.
- **Modes:** none (no `--html`/`--wiki`)
- **Outcome:** Design approved → handoff to `/ck:plan --tdd`.

## Problem statement

The prototype (`s01-brief-list.html`) gained an in-progress "Up next" variant: live score, half label, ticking minute. The production home page has no equivalent. Live match data is *collected* (raw API-Football `status` short codes + scores) but **never reaches the frontend** — every home-page endpoint excludes in-play matches.

## Requirements (confirmed)

- **Expected output:** Home page renders an in-progress card (live score + status/half label + ticking minute) **in place of** the next-match card when ≥1 match is live; normal "Up next" card otherwise.
- **Acceptance criteria:**
  1. Live row in DB ⇒ ticking card replacing next-match, showing score + half label.
  2. Minute re-syncs to real `elapsed` on each ~30s client poll; **Half-time freezes** the tick.
  3. No live match ⇒ current "Up next" behavior unchanged.
  4. Backend live-poller polls `/fixtures?live=all` at **120s, window-gated**; idle (0 quota) outside match windows; never triggers LLM/standings.
  5. `/api/fixtures/live` returns live matches (`elapsed` + `updated_at`), soonest-kicked first, DB-only.
  6. Demoable on free plan via one seeded live row.
- **Scope boundary (OUT):** fixtures-page live rows, knockout, goal-event feed, websockets/push, stacked multi-live cards.
- **Non-negotiable constraints:** `/api/fixtures/upcoming` semantics unchanged; Next.js App Router (read `node_modules/next/dist/docs/` per `frontend/AGENTS.md`); Alembic versioned migrations; reuse existing `.is-live` CSS.
- **Touchpoints:** `backend/app/data/{api_football.py,models.py,collect.py,repository.py}`, `backend/db/migrations/versions/0005_*`, `backend/app/api/fixtures.py`, new `backend/app/pipeline/live_poller.py`; `frontend/lib/api.ts`, `frontend/app/page.tsx`, new `frontend/app/api/live/route.ts`, new `frontend/components/live-match-card.tsx`; tests in `backend/tests/test_fixtures_shaping.py`.

## Key scout findings (the constraints that shaped the design)

- **Live data is collected but hidden.** `_map_fixture` (`api_football.py:69`) stores `status` (`NS/1H/HT/2H/ET/FT…`) + live scores. But `/api/fixtures/upcoming` (`fixtures.py:193`) filters `home_score IS NULL AND kickoff_utc >= now` → live matches (scored, past kickoff) are excluded from every home endpoint.
- **No minute stored.** API-Football returns `fixture.status.elapsed`; `_map_fixture` discards it; `matches_table` has no `elapsed` column. Prototype minute is cosmetic JS.
- **Single-request live fetch exists.** `/fixtures?live=all` returns all in-play games in one call → quota-bounded regardless of match count.
- **Free plan = seasons 2021–2023** (`config.py:11-13`, `API_FOOTBALL_SEASON=2022`). No live 2026 data on free plan; live feature only produces data on a **paid plan during the real tournament**, else degrades to "nothing live" (demoable via seeded row).
- **Refresh cadence.** Daily brief is an Azure Container Apps Job at 07:00 Melbourne (`scheduler_entry.py`); heavy LLM pipeline. Live polling must be a **separate lightweight path**, never re-running standings/LLM.
- **`matches.updated_at` already exists** → freshness anchor for client-side interpolation; no extra column needed for it.

## Approaches evaluated

| # | Approach | Pros | Cons | Verdict |
|---|----------|------|------|---------|
| A | Honest snapshot (no new collection): query stored live row, render score + half label + "as of HH:MM", no ticker | Cheap, truthful, ships today, no migration | Score up to 30 min stale | Recommended as MVP, **not chosen** |
| B | **Real live minute + polling**: capture `elapsed`, fast window-gated poller, `/live` endpoint, client polling + interpolation | Genuine live feel, accurate minute/score | Migration, second scheduler path, API quota, client island | **Chosen** |
| C | Client-derived minute from `now − kickoff` | Visually cheap | Drifts from the stale score beside it; worst of both | Rejected |

## Chosen solution (Approach B) + decisions

**Decisions:** Liveness = real minute + polling · API = new `/api/fixtures/live` · Scope = home only · Multi-live = single soonest-kicked card · Minute = **client interpolation, re-synced per poll** · Poll = **120s window-gated** · Placement = **replaces "Up next" card** · Client path = **Next route-handler proxy**.

### Architecture

```
API-Football ──/fixtures?live=all (1 req)──► live_poller (no LLM/standings)
                                               │ upsert score/status/elapsed/updated_at
                                               ▼
                                           Postgres matches (+ elapsed)
                                               ▲
              GET /api/fixtures/live ──────────┘ (DB only, 0 external quota)
                                               ▲
          Next route handler /api/live (same-origin proxy)
                                               ▲
          <LiveMatchCard> client island ── polls ~30s, ticks minute/sec, freezes on HT
```

### Backend
1. **Migration `0005`** — `matches.elapsed INTEGER NULL`.
2. **Capture** — `Match.elapsed`; `_map_fixture` reads `status_obj.get("elapsed")`.
3. **`get_fixtures(live=True)`** → adds `?live=all`.
4. **`collect_live()`** — upsert only score/status/elapsed/`updated_at` for live fixtures; no standings, no LLM, no prune.
5. **`live_poller.py`** — standalone loop entrypoint (own compose service). Window-gated: polls `?live=all` every 120s only while some fixture ∈ `[kickoff, kickoff+3h]`; long sleep otherwise.
6. **`GET /api/fixtures/live`** — `status ∈ {1H,HT,2H,ET,BT,P,LIVE}`, soonest-kicked first, includes `elapsed` + `updated_at`.

### Frontend
7. `FixtureRow` gains `elapsed`, `updated_at`; `getLiveFixtures()` in `api.ts`.
8. `app/api/live/route.ts` — same-origin proxy to FastAPI.
9. `<LiveMatchCard>` client component — server-seeded initial state, polls `/api/live` every 30s, interpolates minute `elapsed + (now − updated_at)` clamped to half boundaries, freezes/relabels on `HT/BT/P`. Reuses `.is-live` CSS.
10. `page.tsx` — live present ⇒ `<LiveMatchCard>` replaces `<NextMatchCard>`; "Next 2" strip retained; else unchanged.

## Implementation considerations & risks

- **Quota:** window-gating is the safety mechanism; verify match-window detection (kickoff+3h) before merging the poller. Free plan ⇒ no 2026 live data: confirm graceful empty state.
- **Poller runtime:** long-running loop ≠ cron job. Run as its own docker-compose service (fits single-VM infra direction), decoupled from the daily-brief Container Apps Job.
- **Half-time / stoppage:** freeze interpolation on `HT/BT/P`; clamp tick within half (≤45 in 1H, ≤90 in 2H); resync corrects drift.
- **Transition correctness:** match → FT ⇒ `/live` empties ⇒ card disappears, normal up-next returns on next client poll.
- **No regression:** `/api/fixtures/upcoming` untouched; new shaping/endpoint gets tests alongside `test_fixtures_shaping.py`.

## Success metrics / validation

- During a live match (paid plan or seeded row): card shows correct score, ticking minute within ±1 of broadcast at sync, half-time freeze; disappears at FT.
- Poller makes ≤1 API request / 120s, only in windows; 0 requests overnight.
- No live match: home page byte-identical to current behavior.
- `test_fixtures_shaping.py` covers live-filter + soonest-first ordering.

## Next steps / dependencies

- Handoff: `/ck:plan --tdd` with this report as context.
- Dependency for *real* live data: paid API-Football plan covering 2026; otherwise seeded-row demo.
