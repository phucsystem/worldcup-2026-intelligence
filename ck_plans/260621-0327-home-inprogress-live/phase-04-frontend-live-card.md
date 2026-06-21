---
phase: 4
title: Frontend Live Card
status: completed
effort: ''
---

# Phase 4: Frontend Live Card

## Overview

Render the live card on the home page: a client island that seeds from server-fetched live state, polls `/api/live` (same-origin proxy) every ~30s, and ticks an interpolated minute each second, freezing at half-time. When a match is live it replaces the next-match card; otherwise the page is unchanged. Reuses the `.is-live` CSS already in `components.css`/prototype.

Depends on Phase 2 (`GET /api/fixtures/live`).

> Before writing any Next.js code, read the relevant guides in `node_modules/next/dist/docs/` per `frontend/AGENTS.md` (route handlers, client components, dynamic rendering) — this Next version diverges from training data.

## Requirements

- Functional: live present ⇒ `<LiveMatchCard>` shown in the "Up next" section in place of `<NextMatchCard>`; "Next 2" strip retained; no live ⇒ current behavior. Minute = `elapsed + (now − updated_at)`, clamped within the current half, re-synced each poll; `HT`/`BT`/`P` show a frozen label ("Half-time" / "Break" / "Penalties") with no tick.
- Non-functional: backend URL stays server-side (proxy); no CORS; graceful when `/api/live` errors (keep last good state or fall back to next-match).

## Architecture

- **Types** (`lib/api.ts`): `FixtureRow` gains `elapsed: number | null` and `updated_at: string | null`. Add `getLiveFixtures(): Promise<FixtureRow[]>` hitting `/api/fixtures/live` (server-side, uses `API_BASE`). Decide bare-list vs wrapper to match P2 (recommend bare list).
- **Proxy** (`app/api/live/route.ts`): a Next route handler that fetches `${API_BASE}/api/fixtures/live` server-side and returns the JSON; `export const dynamic = "force-dynamic"` / `no-store`. Client polls this same-origin path.
- **Pure helper** (`lib/live.ts`): `liveMinute(elapsed, updatedAtIso, status, nowMs)` → `{ minute, frozen, label }`. Encapsulates interpolation + half clamping (1H cap 45, 2H cap 90) + HT/BT/P freeze. Pure ⇒ unit-testable if infra exists.
- **Client island** (`components/live-match-card.tsx`, `"use client"`): props `initial: FixtureRow`. `useState` seeded from `initial`; `useEffect` interval (30s) `fetch("/api/live")` → pick soonest-kicked → update state; second interval (1s) recomputes displayed minute via `liveMinute`. Renders the `.is-live` markup (eyebrow "Live now · {label}", `.nm-score`, `.nm-live-clock` minute). On fetch error: keep current state; if list becomes empty, signal "no longer live" (component renders null, or parent re-fetches on navigation).
- **Page** (`app/page.tsx`, server): add `getLiveFixtures()` to the `Promise.all`; compute `live = liveFixtures[0] ?? null`. In the "Up next" section: `live ? <LiveMatchCard initial={live} /> : <NextMatchCard ... />`. Keep `CompactFixtureStrip` as-is. The section's render condition becomes `(live || upNext || nextFixtures.length)`.

## Related Code Files

- Create: `frontend/app/api/live/route.ts`
- Create: `frontend/components/live-match-card.tsx`
- Create: `frontend/lib/live.ts` (pure minute helper)
- Modify: `frontend/lib/api.ts` (types + `getLiveFixtures`)
- Modify: `frontend/app/page.tsx` (lead-card swap)
- Reuse (no change expected): `.is-live` styles in `frontend/app/globals.css` — verify the prototype's `.is-live`/`.nm-score`/`.nm-live-clock` rules exist in the app CSS; if not, port them from `prototypes/components.css`.

## Implementation Steps (TDD where infra allows)

1. Check for a frontend test runner (vitest/jest in `frontend/package.json`). If present: **test first** — `lib/live.test.ts` for `liveMinute`: `2H, elapsed 67, updated 40s ago` ⇒ minute 67 (40s < 60s, no bump) then ≥68 after 60s; `HT` ⇒ `{frozen:true, label:"Half-time"}`; `1H, elapsed 44, +90s` ⇒ clamped at 45. If no runner exists, implement `liveMinute` as a pure function and validate via a temporary node script; note the gap.
2. Implement `lib/live.ts` `liveMinute(...)`. Run helper tests → green.
3. Add `FixtureRow` fields + `getLiveFixtures()` in `api.ts`.
4. Add `app/api/live/route.ts` proxy (server fetch + no-store). Verify `curl localhost:3000/api/live` proxies the backend.
5. Verify `.is-live` CSS is present in the app; port from prototype if missing.
6. Build `components/live-match-card.tsx` client island (poll + tick + render). Handle empty/error.
7. Wire `app/page.tsx`: fetch live, swap lead card.
8. Verify against a **seeded live row** (P3 `seed_live_match.py`): card appears in place of next-match, minute ticks, HT freezes; delete/flip seed to FT ⇒ card disappears and next-match returns. Confirm no-live path is unchanged.

## Success Criteria

- [ ] `liveMinute` covers interpolation, half clamp, and HT/BT/P freeze (unit-tested if a runner exists; otherwise validated manually with the gap noted).
- [ ] `/api/live` proxy returns backend live JSON same-origin (no CORS, backend URL not exposed to client).
- [ ] With a seeded live row, the home page shows the live card in place of next-match, minute ticking, half-time frozen.
- [ ] With no live row, the home page is unchanged vs current.
- [ ] At FT (seed flipped), the card disappears and the normal next-match card returns.

## Risk Assessment

- **Client can't use server `API_BASE`**: the proxy is the fix; do not call FastAPI directly from the client island.
- **Polling churn / leaks**: clear both intervals on unmount; avoid overlapping fetches (guard with an in-flight flag).
- **Clock skew**: `now − updated_at` uses client clock vs server timestamp; small skew is corrected each poll. Acceptable for a minute display.
- **CSS drift**: app CSS may not yet have `.is-live` (prototype-only). Step 5 explicitly verifies/ports it.
