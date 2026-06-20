import type { TournamentSummary } from "@/lib/api";

interface Props {
  summary: TournamentSummary | null;
  dateLabel: string;
  freshLabel?: string;
}

export default function SummaryPanel({
  summary,
  dateLabel,
  freshLabel = "Updated 7:00 AM AEST",
}: Props) {
  if (!summary) return null;

  return (
    <section className="summary-panel" aria-label="Tournament summary">
      <div className="sp-top">
        <div className="sp-headline">
          <span className="sp-eyebrow">World Cup 2026 · Daily Intelligence</span>
          <p className="sp-date">{dateLabel}</p>
        </div>
        <span className="fresh-pill">
          <span className="fp-dot" /> {freshLabel}
        </span>
      </div>

      <div className="sp-stats">
        <div className="ts-stat">
          <span className="ts-value">{summary.stage}</span>
          <span className="ts-label">Stage</span>
        </div>
        <div className="ts-stat">
          <span className="ts-value">
            Matchday {summary.matchday}
            <span className="ts-sub">/{summary.matchday_total}</span>
          </span>
          <span className="ts-label">Round</span>
        </div>
        <div className="ts-stat">
          <span className="ts-value">
            {summary.teams_remaining}
            <span className="ts-sub">/{summary.teams_total}</span>
          </span>
          <span className="ts-label">Teams remaining</span>
        </div>
        {summary.days_to_next_phase !== null && (
          <div className="ts-stat accent">
            <span className="ts-value">{summary.days_to_next_phase} days</span>
            <span className="ts-label">
              {summary.next_phase_label ? `To ${summary.next_phase_label}` : "To next phase"}
            </span>
          </div>
        )}
      </div>

      <div className="sp-progress">
        <div className="sp-progress-track">
          <div className="sp-progress-fill" style={{ width: `${summary.group_stage_pct}%` }} />
        </div>
        <span className="sp-progress-label">
          Group stage {summary.group_stage_pct}% complete
        </span>
      </div>
    </section>
  );
}
