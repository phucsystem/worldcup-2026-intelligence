---
title: Home Page In-Progress (Live) Match Section
description: ''
status: completed
priority: P2
branch: main
tags: []
blockedBy: []
blocks: []
created: '2026-06-20T17:32:29.039Z'
createdBy: 'ck:plan'
source: skill
---

# Home Page In-Progress (Live) Match Section

## Overview

Back the prototype's in-progress "Up next" variant with real data. When ≥1 match is live, the home page shows a single live card (score + half label + ticking minute) that **replaces** the next-match card; otherwise behavior is unchanged. The minute ticks client-side and re-syncs to a real `elapsed` value fetched on a poll. A separate lightweight, window-gated backend poller refreshes live scores without re-running the LLM/standings pipeline.

Approach, decisions, and scout findings: `ck_plans/reports/brainstorm-260621-home-inprogress-live-section.md`.

**Mode:** `--tdd` — each phase writes failing tests first, then implements to green. Pure shaping/mapping/window logic is unit-tested; the frontend client island is verified via a seeded live row.

## Acceptance Criteria (whole plan)

1. A live row in the DB ⇒ home renders the live card in place of the next-match card, with live score + half label.
2. The minute re-syncs to backend `elapsed` on each poll and ticks each second; **half-time freezes** the tick.
3. No live match ⇒ home page behavior is byte-identical to current.
4. The poller polls `/fixtures?live=all` at 120s **only inside match windows**; idle (0 external requests) otherwise; never triggers LLM/standings/prune.
5. `GET /api/fixtures/live` returns live matches (`elapsed` + `updated_at`), soonest-kicked first, reading the DB only.
6. `/api/fixtures/upcoming` semantics are unchanged.
7. Feature is demoable on the free API plan via a seeded live row.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Backend Data Capture](./phase-01-backend-data-capture.md) | Completed |
| 2 | [Live API Endpoint](./phase-02-live-api-endpoint.md) | Completed |
| 3 | [Live Poller](./phase-03-live-poller.md) | Completed |
| 4 | [Frontend Live Card](./phase-04-frontend-live-card.md) | Completed |

**Build order / dependencies:** P1 → P2 → P4; P1 → P3. P2 and P3 are independent (both need P1's `elapsed`). P4 needs P2's endpoint.

## Dependencies

- **Cross-plan (soft):** `260621-azure-vm-deploy` enumerates the compose services (postgres + backend + scheduler + Next SSR). Phase 3 adds a `live_poller` service; that deploy plan's service list must be updated to include it before/at deploy. Not a hard block — the app ships correctly without the poller running (live section simply stays empty).
- **Shared file (no conflict):** `260620-1752-home-page-design-parity-v2` also edits `frontend/app/page.tsx`. This plan's change is additive (conditional live card in the "Up next" section). Coordinate merge order if both are in flight.
- **External:** Real live data requires a paid API-Football plan covering season 2026. On the free plan (`API_FOOTBALL_SEASON=2022`) `?live=all` returns nothing for 2026 — the feature degrades to "no live match" and is demoed via the Phase 3 seed helper.

## Out of Scope

Fixtures-page live rows, knockout live state, goal-event feed, websockets/push, stacked multi-live cards.
