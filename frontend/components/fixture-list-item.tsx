import type { FixtureRow } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import { kickoffTime, weekdayShort } from "@/lib/time";

interface Props {
  fixture: FixtureRow;
  stakeText?: string;
}

export default function FixtureListItem({ fixture, stakeText }: Props) {
  return (
    <div className="fixture-row">
      <div className="fixture-time">
        {kickoffTime(fixture.kickoff_utc)}
        <span className="ft-tz">{weekdayShort(fixture.kickoff_utc)}</span>
      </div>
      <div className="fixture-teams">
        <span className="fixture-team">
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={18} />
          {fixture.home_team ?? "TBD"}
        </span>
        <span className="fixture-vs">vs</span>
        <span className="fixture-team">
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={18} />
          {fixture.away_team ?? "TBD"}
        </span>
        {stakeText && <span className="fixture-stake">{stakeText}</span>}
      </div>
      <div className="fixture-meta">
        {fixture.group_name && <span className="group-pill">{fixture.group_name}</span>}
      </div>
    </div>
  );
}
