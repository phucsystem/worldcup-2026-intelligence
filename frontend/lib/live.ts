// Pure helpers for the in-progress (live) match card. No React, no DOM — so the
// minute interpolation + half-clamp + freeze logic is unit-tested directly.

export interface LiveMinute {
  minute: number | null;
  frozen: boolean;
  label: string;
}

// status → display label. Frozen statuses don't tick (the clock is paused).
const LABELS: Record<string, string> = {
  "1H": "1st half",
  "2H": "2nd half",
  ET: "Extra time",
  HT: "Half-time",
  BT: "Break",
  P: "Penalties",
};

const FROZEN = new Set(["HT", "BT", "P"]);

// Generous per-half ceiling: high enough that normal stoppage time still ticks
// (a hard 45/90 reads as a stuck clock during stoppage), low enough to bound a
// runaway interpolation if polling ever wedges. Each poll re-syncs to the real
// elapsed, so this only caps the gap between syncs.
const CAP: Record<string, number> = { "1H": 50, "2H": 100, ET: 130 };

export function liveMinute(
  elapsed: number | null,
  updatedAtIso: string | null,
  status: string | null,
  nowMs: number,
): LiveMinute {
  const code = (status ?? "").toUpperCase();
  const label = LABELS[code] ?? "Live";
  const frozen = FROZEN.has(code);

  if (elapsed == null) return { minute: null, frozen, label };
  if (frozen) return { minute: elapsed, frozen, label };

  let minute = elapsed;
  if (updatedAtIso) {
    const updatedMs = Date.parse(updatedAtIso);
    if (!Number.isNaN(updatedMs)) {
      const bumped = Math.floor((nowMs - updatedMs) / 60_000);
      if (bumped > 0) minute = elapsed + bumped;
    }
  }
  const cap = CAP[code];
  if (cap != null && minute > cap) minute = cap;
  return { minute, frozen, label };
}
