"use client";

import { useEffect, useState } from "react";

interface Props {
  kickoffUtc: string | null;
  className?: string;
  variant?: "inline" | "tiles";
}

type Parts = { d: number; h: number; m: number; s: number };

function parts(msRemaining: number): Parts {
  const total = Math.floor(msRemaining / 1000);
  return {
    d: Math.floor(total / 86400),
    h: Math.floor((total % 86400) / 3600),
    m: Math.floor((total % 3600) / 60),
    s: total % 60,
  };
}

function inlineLabel({ d, h, m, s }: Parts): string {
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

const pad = (n: number) => (n < 10 ? `0${n}` : String(n));

function Segment({ num, label }: { num: number; label: string }) {
  return (
    <span className="cd-seg">
      <span className="cd-num">{pad(num)}</span>
      <span className="cd-lbl">{label}</span>
    </span>
  );
}

/**
 * Live countdown to kickoff. Rolls to "LIVE" at zero. Decorative
 * (`aria-hidden`) — screen readers get the static kickoff time from the
 * surrounding fixture row. Renders a stable placeholder until mounted to avoid
 * hydration mismatch, and honors prefers-reduced-motion (no per-second churn).
 * `variant="tiles"` renders segmented HRS/MIN/SEC tiles (Up-next banner);
 * `variant="inline"` (default) renders a compact "in 5h 25m" string.
 */
export default function Countdown({ kickoffUtc, className, variant = "inline" }: Props) {
  const [remaining, setRemaining] = useState<number | null>(null);

  useEffect(() => {
    if (!kickoffUtc) return;
    const target = new Date(kickoffUtc).getTime();
    if (Number.isNaN(target)) return;

    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    const tick = () => {
      const diff = target - Date.now();
      setRemaining(diff);
      return diff;
    };

    tick();
    // Reduced motion: update once per minute instead of every second.
    const interval = reduced ? 60_000 : 1_000;
    const id = window.setInterval(() => {
      if (tick() <= 0) window.clearInterval(id);
    }, interval);
    return () => window.clearInterval(id);
  }, [kickoffUtc]);

  if (remaining === null) {
    if (variant === "tiles") {
      return (
        <span aria-hidden="true" className="countdown" style={{ color: "#6B7A9E" }}>
          —
        </span>
      );
    }
    return (
      <span aria-hidden="true" className={className} style={{ color: "#6B7A9E" }}>
        —
      </span>
    );
  }

  const isLive = remaining <= 0;

  if (variant === "tiles") {
    if (isLive) {
      return (
        <span aria-hidden="true" className="countdown">
          <span className="cd-live">LIVE</span>
        </span>
      );
    }
    const p = parts(remaining);
    return (
      <span aria-hidden="true" className="countdown">
        {p.d > 0 && <Segment num={p.d} label="days" />}
        <Segment num={p.h} label="hrs" />
        <Segment num={p.m} label="min" />
        <Segment num={p.s} label="sec" />
      </span>
    );
  }

  return (
    <span
      aria-hidden="true"
      className={className}
      style={{
        color: isLive ? "#FF5A5A" : "#4D8BFF",
        fontVariantNumeric: "tabular-nums",
        fontWeight: 600,
      }}
    >
      {isLive ? "LIVE" : `in ${inlineLabel(parts(remaining))}`}
    </span>
  );
}
