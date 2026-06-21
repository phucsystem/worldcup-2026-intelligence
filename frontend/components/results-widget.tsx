"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ResultWidgetRow } from "@/lib/results";
import TeamFlag from "@/components/team-flag";

/**
 * Latest Results — ABC-style center-anchored list with a "Display in Groups"
 * toggle. Flat view is block flow (DOM order); grouped view switches to flexbox
 * so each row's precomputed `order` clusters it under its group header. Inline
 * `order` is set on every row/header (inert in flat mode), so server and client
 * markup are identical — no hydration mismatch.
 */
export default function ResultsWidget({ rows }: { rows: ResultWidgetRow[] }) {
  const [grouped, setGrouped] = useState(true);

  const groups = useMemo(() => {
    const g: string[] = [];
    for (const r of rows) if (!g.includes(r.group)) g.push(r.group);
    return g.sort();
  }, [rows]);

  if (!rows || rows.length === 0) return null;

  const counters: Record<number, number> = {};
  const rowOrder = rows.map((r) => {
    const gi = groups.indexOf(r.group);
    counters[gi] = (counters[gi] || 0) + 1;
    return gi * 100 + counters[gi];
  });

  return (
    <section className={`results-widget${grouped ? " grouped" : ""}`}>
      <div className="rw-head">
        <h2 className="rw-title">Latest Results</h2>
      </div>

      <label className="rw-toggle-bar">
        <span className="rw-tg-label">Display in Groups</span>
        <input
          type="checkbox"
          hidden
          checked={grouped}
          onChange={(e) => setGrouped(e.target.checked)}
        />
        <span className="rw-switch" aria-hidden="true" />
        <span className="rw-tg-state">{grouped ? "On" : "Off"}</span>
      </label>

      <div className="rw-list">
        {rows.map((r, i) => {
          const winHome = r.winner === "home";
          const winAway = r.winner === "away";
          return (
            <Link
              key={r.key}
              href={`/brief/${r.briefDate}`}
              className={`match-row${winHome ? " winner-home" : ""}${winAway ? " winner-away" : ""}`}
              style={{ order: rowOrder[i] }}
            >
              <span className="mr-date">{r.dateLabel}</span>
              <span className={`mr-team home${winAway ? " lose" : ""}`}>
                <span className="mr-name">{r.home}</span>
                <TeamFlag team={r.home} size={18} />
              </span>
              <span className={`mr-score${winHome ? " win" : ""}`}>{r.homeScore}</span>
              <span className="mr-center">
                <span className="mr-group">{r.group}</span>
                <span className="mr-status">Full Time</span>
              </span>
              <span className={`mr-score${winAway ? " win" : ""}`}>{r.awayScore}</span>
              <span className={`mr-team away${winHome ? " lose" : ""}`}>
                <TeamFlag team={r.away} size={18} />
                <span className="mr-name">{r.away}</span>
              </span>
              <span className="mr-arrow">→</span>
            </Link>
          );
        })}

        {groups.map((g, i) => (
          <div key={g} className="rw-group-header" style={{ order: i * 100 }}>
            {g}
          </div>
        ))}
      </div>
    </section>
  );
}
