"use client";

import { useEffect, useState, type CSSProperties } from "react";

// SSR and the first client render use this fixed zone so the markup matches at
// hydration; after mount we switch to the viewer's actual zone. The server
// can't know the browser timezone, so localized instants must resolve client-side.
export const FALLBACK_TZ = "Australia/Melbourne";

type Mode = "time" | "day" | "dayTime" | "zone";

interface Props {
  iso: string | null;
  mode?: Mode;
  withZone?: boolean;
  className?: string;
  style?: CSSProperties;
}

export function resolveTz(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || FALLBACK_TZ;
  } catch {
    return FALLBACK_TZ;
  }
}

export function zoneAbbr(d: Date, tz: string): string {
  // Fixed en-AU locale: the canonical zone (Australia/Melbourne) reads as
  // "AEST" — brand-consistent and hydration-stable — while other zones render
  // as an unambiguous GMT offset (e.g. "GMT+1") for non-AU viewers.
  const parts = new Intl.DateTimeFormat("en-AU", {
    timeZone: tz,
    hour: "2-digit",
    timeZoneName: "short",
  }).formatToParts(d);
  return parts.find((p) => p.type === "timeZoneName")?.value ?? "";
}

function render(iso: string, tz: string, mode: Mode, withZone: boolean): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "TBD";
  if (mode === "zone") return zoneAbbr(d, tz);

  const day = d.toLocaleDateString("en-AU", {
    timeZone: tz,
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  if (mode === "day") return day;

  let time = d.toLocaleTimeString("en-AU", {
    timeZone: tz,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  if (withZone) time = `${time} ${zoneAbbr(d, tz)}`;
  if (mode === "time") return time;
  return `${day} · ${time}`;
}

/**
 * Renders a UTC instant in the viewer's browser timezone. Hydration-safe:
 * first paint uses FALLBACK_TZ (matching SSR), then re-renders in the resolved
 * zone after mount. Editorial calendar dates (brief/archive/snapshot) are NOT
 * instants and should keep their fixed-timezone formatting instead.
 */
export default function LocalTime({ iso, mode = "time", withZone = false, className, style }: Props) {
  const [tz, setTz] = useState(FALLBACK_TZ);
  useEffect(() => {
    setTz(resolveTz());
  }, []);

  if (!iso) {
    return (
      <span className={className} style={style}>
        TBD
      </span>
    );
  }
  return (
    <span className={className} style={style} suppressHydrationWarning>
      {render(iso, tz, mode, withZone)}
    </span>
  );
}

/** Inline note for page headers: "Times in your timezone (BST)". */
export function TimezoneNote({ className, style }: { className?: string; style?: CSSProperties }) {
  const [tz, setTz] = useState(FALLBACK_TZ);
  useEffect(() => {
    setTz(resolveTz());
  }, []);
  const abbr = zoneAbbr(new Date(), tz);
  const where = tz === FALLBACK_TZ ? "Australia/Melbourne" : "your timezone";
  return (
    <span className={className} style={style} suppressHydrationWarning>
      Times in {where} ({abbr})
    </span>
  );
}
