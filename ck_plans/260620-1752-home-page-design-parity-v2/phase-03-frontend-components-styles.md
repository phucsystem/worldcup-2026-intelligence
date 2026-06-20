---
phase: 3
title: "Frontend Components & Styles"
status: pending
effort: "L"
dependencies: [2]
---

# Phase 3: Frontend Components & Styles

## Overview

Port the new prototype CSS into `globals.css`, extend the API client types/fetchers to match Phase-2 contracts, and build the new presentational (server) components. No page wiring yet (Phase 4) and no client interactivity except where unavoidable.

## Requirements

- Functional: `globals.css` carries all new component classes; `lib/api.ts` exposes `intelligence` on `BriefDetail` + `getTournamentSummary()`; new components render from props.
- Non-functional: components are server components (except `ResultsWidget`, Phase 4); graceful-degrade when props empty; reuse existing `TeamFlag`/`Countdown`.

## Architecture

```
SummaryPanel({ summary, dateLabel, freshLabel })            -> .summary-panel ... .sp-progress
NextMatchCard({ fixture, stakeText })                        -> a.next-match (football-sphere)
FixtureListItem({ fixture, stakeText })                      -> .fixture-row + .fixture-stake
StakeGrid({ scenarios })  / StakeCard({ scenario })          -> .stake-grid / .stake-card + .sk-table
ResultsWidget(...)        -> Phase 4 (client)
```

CSS port: copy the new blocks from `prototypes/components.css` into `frontend/app/globals.css` — Latest Results widget (`.results-widget`…`.rw-group-header` + its media query), Summary panel (`.summary-panel`…`.sp-progress-label` + media query), stake lines (`.nm-stake`, `.fixture-stake`), What's-at-stake (`.stake-grid`…`.sk-note`), Up-next next-match (`.next-match`…`.nm-countdown-wrap` + glass countdown), and any missing `.fixture-*`/`.flag-svg`/`.countdown` rules the new components rely on. Confirm CSS variables used (`--surface`, `--status-live`, `--accent-bright`, `--space-*`, `--radius-*`) resolve in `globals.css`; map/add any missing tokens to the existing `--color-*` set.

## Related Code Files

- Modify: `frontend/app/globals.css` — append ported component classes (guard against duplicating the ~11 already present: `.result-chip`, `.chip-row`, `.rc-letter`, `.win/.draw/.loss`, `.sparkline`, `.skeleton-*`, `.tabular-nums`).
- Modify: `frontend/lib/api.ts` — add `intelligence?: Intelligence | null` to `BriefDetail`; add `Intelligence`, `FixtureStake`, `GroupScenario`, `ScenarioRow`, `TournamentSummary` interfaces; add `getTournamentSummary()`.
- Create: `frontend/components/summary-panel.tsx` (server).
- Create: `frontend/components/next-match-card.tsx` (server; wraps `TeamFlag` + `Countdown`).
- Create: `frontend/components/fixture-list-item.tsx` (server; `.fixture-row` with optional `.fixture-stake`).
- Create: `frontend/components/stake-grid.tsx` + `stake-card.tsx` (server).
- Create: `frontend/lib/stakes.ts` — pure helper mapping `intelligence.fixture_stakes` → `Map<fixture_id, stake_text>` and merging `group_scenarios` line/tag with deterministic `rows`.

## Implementation Steps

1. Extend `lib/api.ts` types + add `getTournamentSummary()` (mirrors existing `apiFetch` pattern, returns `null` on failure).
2. Port CSS blocks into `globals.css`; verify token names. Do not re-add existing classes.
3. `lib/stakes.ts`: `stakesByFixtureId(intelligence)` and `scenariosForDisplay(intelligence)` (only groups with both an LLM line and deterministic rows).
4. `SummaryPanel`: render eyebrow + date + fresh-pill + `.sp-stats` (stage, matchday `x/total`, teams `remaining/total`, accent days-to-next-phase) + `.sp-progress` (width from `group_stage_pct`). Hide when `summary` null. **Omit the days-to-next-phase `.ts-stat` cell entirely when `days_to_next_phase` is null** (knockout not yet scheduled). <!-- Updated: Validation Session 1 - hide days-to-phase cell when null -->
5. `NextMatchCard`: `a.next-match` linking to `/fixtures`; `.nm-side` flags + names via `TeamFlag`; `.nm-meta` (kickoff AEST + group); `.nm-countdown-wrap` with `Countdown`; optional `.nm-stake` line. Reuse `kickoffTime` logic from `fixture-row.tsx` (extract to a shared util or duplicate the small helper).
6. `FixtureListItem`: `.fixture-row` grid (time/teams/meta) with optional `.fixture-stake` under the teams + `.group-pill`.
7. `StakeCard`/`StakeGrid`: `.sk-head` (group + `.sk-tag`, `.live` when tag implies imminent), `.sk-line`, `.sk-table` rows with `.sk-pos/.sk-team/.sk-pts/.sk-note` (note css class from `status`).
8. Typecheck/build (`cd frontend`); fix type errors. Components not yet mounted — verify they compile in isolation (e.g. temporary import or `tsc --noEmit`).

## Success Criteria

- [ ] `globals.css` contains all new classes; no duplicate selectors with existing ones; tokens resolve.
- [ ] `lib/api.ts` compiles with new types; `getTournamentSummary()` present.
- [ ] All five new components compile and render correctly from sample props (no runtime errors).
- [ ] Components graceful-degrade (return `null`) on empty/missing props.
- [ ] Frontend typecheck/build passes.

## Risk Assessment

- **CSS variable mismatch** — prototype uses `--surface`, `--space-4`, etc.; `globals.css` defines `--color-*`. Audit and add aliases/missing tokens before porting, or the panels render unstyled.
- **Hydration**: keep date/time formatting anchored to a fixed timezone (Australia/Melbourne) as existing components do — avoid `new Date()` locale drift (prior hydration bug, see app history).
- **Next.js version caveat** (`frontend/AGENTS.md`): consult `node_modules/next/dist/docs/` before using framework APIs that may differ from training data.
- **Football-sphere `::after`** uses an inline SVG data-URI mask — verify it survives the CSS port verbatim (escaping).
