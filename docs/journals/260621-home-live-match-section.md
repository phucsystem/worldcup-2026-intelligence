# Home Page In-Progress (Live) Match Section

**Date:** 2026-06-21
**Branch:** `feat/home-live-match-section` (`afca9028`)
**Plan:** `ck_plans/260621-0327-home-inprogress-live/` · **Flow:** brainstorm → plan (`--tdd`) → cook, 4 TDD phases

## What shipped

When a match is in play, the home page now leads with a live card — live score, half label, and a minute that ticks each second and re-syncs to the real `elapsed` on every poll — replacing the next-match card. Falls back to the normal "Up next" card when nothing is live.

- **Data (P1):** `matches.elapsed` (migration `0005`, reverses cleanly), captured from API-Football `status.elapsed`; `get_fixtures(live=True)` → `?live=all` (one request, all in-play games).
- **API (P2):** `GET /api/fixtures/live` — DB-only, soonest-kicked first, pure `shape_live`/`is_live_status`. `FixtureRow` gained `elapsed` + `updated_at`. `/api/fixtures/upcoming` untouched.
- **Poller (P3):** standalone `live_poller.py` — window-gated (polls `?live=all` every 120s only while a fixture is in `[kickoff, kickoff+3h]`; idle/zero-quota otherwise). Never runs standings/LLM/prune. `collect_live` is cross-league-safe (intersects `?live=all` with stored `fixture_id`s). `seed_live_match.py` demo helper + `live_poller` compose service.
- **Frontend (P4):** pure `liveMinute` interpolation (half-time freeze, stoppage-aware caps), same-origin `/api/live` proxy (keeps backend URL server-side, no CORS), `<LiveMatchCard>` client island, `page.tsx` lead-card swap, ported `.is-live` CSS.

## Decisions

- **Real minute + polling** over an honest snapshot — the user chose accuracy over the cheaper "as of HH:MM" approach despite the larger surface.
- **Client interpolation re-synced per poll** — smooth tick anchored to `updated_at`, corrected each 30s fetch; `nowMs` seeded from `updated_at` for hydration safety.
- **Live card replaces** the next-match card (not stacked); single soonest-kicked card.

## Code review caught two real bugs (both fixed)

- **H1 — finished match stuck "live":** a finished match drops out of `?live=all`, so the poller never writes its `FT` status; only the full hourly collect does. Added a kickoff-window guard to `get_live()` so a stale live row stops rendering before the next collect.
- **H2 — stoppage-time stuck clock:** the hard 45/90 minute clamp froze the clock during stoppage. Relaxed caps (50/100/130) so stoppage ticks while still bounding runaway interpolation.

## Gotchas / follow-ups

- **Free API-Football plan has no 2026 live data** (`API_FOOTBALL_SEASON=2022`); feature degrades to "nothing live" and is demoable via `python -m app.data.seed_live_match`.
- **Running Docker containers were pre-change** — the live app showed `[]` until rebuilt: `docker compose up -d --build backend frontend live_poller`.
- **Deploy plan `260621-azure-vm-deploy` needs updating** — add the new `live_poller` service + env vars (`LIVE_POLL_SECONDS`, `IDLE_SLEEP_SECONDS`, `LIVE_WINDOW_HOURS`).

## Verification

Backend 97 tests · frontend 21 tests + tsc + eslint + production build — all green. Migration up/down roundtrip verified; `/live` and `/upcoming` smoke-tested against the real DB; H1 window guard confirmed (recent live match shows, stale one excluded).
