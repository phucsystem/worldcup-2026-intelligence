---
phase: 4
title: "Frontend Integration & Verification"
status: pending
effort: "M"
dependencies: [3]
---

# Phase 4: Frontend Integration & Verification

## Overview

Build the one stateful component (`ResultsWidget`), rewire `page.tsx` to the prototype section order with all data wired, and verify visual + functional parity end-to-end.

## Requirements

- Functional: `ResultsWidget` renders grouped/flat match list with a working "Display in Groups" toggle; `page.tsx` shows all sections in prototype order; every section reads real data; Stars + Earlier retained.
- Non-functional: only `ResultsWidget` is `"use client"`; SSR-safe; reduced-motion respected; mobile layout intact.

## Architecture

```
page.tsx (server) fetches in parallel:
  getLatestBrief()  getTournamentSummary()  getUpcomingFixtures()
  getStars()  getStandings()  listBriefs()

Section order (prototype parity):
  1 SummaryPanel            <- tournament summary
  2 Up next: NextMatchCard  <- upcoming.up_next + stakesByFixtureId
    + FixtureListItem x2     <- next 2 from upcoming.days (flattened)
    + "See all fixtures →"
  3 Today's brief: HeroBriefCard + ResultChips   <- latest + recentResultStrip
  4 ResultsWidget (client)  <- recentResultStrip (more rows, grouped)
  5 StakeGrid               <- intelligence.group_scenarios (merged)
  6 Stars to watch (kept)   <- topStars
  7 Earlier (kept)          <- earlier briefs grid + archive link
  EmptyState when latest null
```

`ResultsWidget` port of `interactions.js` (lines ~143–172): a `"use client"` component holding `grouped` state; flat view = block flow (DOM order), grouped view = flex with `order` computed per row (`groupIndex*100 + counter`) and `.rw-group-header` elements ordered by group. Reuse the prototype's `.results-widget.grouped` class toggle + the `.rw-toggle-bar` switch markup.

## Related Code Files

- Create: `frontend/components/results-widget.tsx` (`"use client"`).
- Modify: `frontend/app/page.tsx` — import new components; reorder sections; wire data; keep `recentResultStrip` (extend `limit` for the widget); keep Stars + Earlier blocks.
- Modify: `frontend/lib/results.ts` (if needed) — add a grouped mapping helper (date label + group) for the widget rows.
- Reference: `prototypes/s01-brief-list.html` (target markup/order), `prototypes/interactions.js` (toggle logic).

## Implementation Steps

1. Build `ResultsWidget`: props = match rows (with `group_name`, date label, home/away, scores, winner flag). Local `useState` for `grouped`; compute `order` for rows + headers in grouped mode; render `.rw-toggle-bar` switch wired to state; rows are `Link`s to `/brief/{date}` like the prototype's `s02` links (or to the relevant brief). Respect `prefers-reduced-motion` via existing CSS.
2. Map data for the widget from `standings.recent_results` (reuse/extend `recentResultStrip`); derive a human date label (anchored to a fixed timezone to avoid hydration drift) + `group_name` per row.
3. Rewire `page.tsx`: add the parallel `getTournamentSummary()` fetch; render sections 1–7 in the order above; pass `stakesByFixtureId(latest?.intelligence)` to `NextMatchCard` + `FixtureListItem`; pass `scenariosForDisplay(latest?.intelligence)` to `StakeGrid`; flatten `upcoming.days` for the 2 fixture rows; keep the "See all fixtures →" link to `/fixtures`.
4. Ensure every section conditionally renders (no crash when summary/intelligence/upcoming empty) — mirror existing `{x && (...)}` guards.
5. Verify: `cd frontend && <build>` clean; run app + backend; **trigger `POST /api/admin/run-brief` once** (the latest published brief predates Phase-2 code, so its `intelligence` is null until a fresh run); then load home page; confirm all five sections render with real data, toggle works, mobile layout holds, no console/hydration errors. <!-- Updated: Validation Session 1 - run-brief is a mandatory verification step; ~8 widget rows link to /brief/{date} -->
6. Optional visual check: screenshot home page vs `prototypes/s01-brief-list.html` for parity (the prior plan used a screenshot-diff loop).

## Success Criteria

- [ ] Home page renders sections in prototype order; Stars + Earlier present.
- [ ] `ResultsWidget` toggle switches grouped/flat correctly, SSR-safe, no hydration warning.
- [ ] Next-match card + fixture rows show stakes (when present); StakeGrid shows group cards with correct per-team notes.
- [ ] Summary panel figures correct vs current data.
- [ ] All sections graceful-degrade when data absent.
- [ ] `cd frontend` build/typecheck passes; no console errors on load.

## Risk Assessment

- **Client/server boundary**: only `ResultsWidget` may be `"use client"`; passing server-fetched plain data as props is fine. Don't make `page.tsx` client.
- **Hydration mismatch** on date labels (known prior bug) → format on the server with a fixed timezone; pass strings into the client widget rather than formatting client-side.
- **Stakes mismatch**: render a fixture's stake only when its `fixture_id` is in the LLM map; otherwise omit silently (no placeholder).
- **`order`-based grouped layout** depends on the ported `.results-widget.grouped` flex CSS from Phase 3 — verify those rules landed.
- **Empty `intelligence`** on first load → expected until a brief runs with Phase-2 code; documented mitigation is `/api/admin/run-brief`.
