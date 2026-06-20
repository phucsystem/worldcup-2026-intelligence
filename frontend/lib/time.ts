// Kickoff formatting anchored to a fixed timezone so server- and client-rendered
// output always match (avoids the locale-drift hydration bug). Mirrors the
// inline helper in fixture-row.tsx.
const TZ = "Australia/Melbourne";

export function kickoffTime(iso: string | null): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "TBD";
  return d.toLocaleTimeString("en-AU", {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function kickoffDayLabel(iso: string | null): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "TBD";
  return d.toLocaleDateString("en-AU", {
    timeZone: TZ,
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

export function weekdayShort(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-AU", { timeZone: TZ, weekday: "short" });
}

/** YYYY-MM-DD in the brief timezone — used to build /brief/{date} links. */
export function dateKey(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-CA", { timeZone: TZ });
}
