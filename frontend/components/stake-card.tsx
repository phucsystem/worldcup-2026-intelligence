import type { GroupScenario } from "@/lib/api";
import TeamFlag from "@/components/team-flag";

// A tag implies an imminent decision (live styling) when it reads like "tonight".
function isLiveTag(tag: string): boolean {
  return /tonight|live|today|now/i.test(tag);
}

export default function StakeCard({ scenario }: { scenario: GroupScenario }) {
  return (
    <article className="stake-card">
      <header className="sk-head">
        <span className="sk-group">{scenario.group_name}</span>
        <span className={`sk-tag${isLiveTag(scenario.tag) ? " live" : ""}`}>{scenario.tag}</span>
      </header>
      <p className="sk-line">{scenario.line}</p>
      <ul className="sk-table">
        {(scenario.rows ?? []).map((r) => (
          <li key={r.team}>
            <span className="sk-pos">{r.position}</span>
            <span className="sk-team">
              <TeamFlag team={r.team} size={18} />
              {r.team}
            </span>
            <span className="sk-pts">{r.points} pts</span>
            <span className={`sk-note ${r.status}`}>{r.note}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}
