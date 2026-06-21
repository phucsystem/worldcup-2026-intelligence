from collections import defaultdict

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.data.models import Match, StandingRow
from app.data.repository import make_engine, make_session_factory, matches_table
from app.data.standings_math import compute_group_table, tournament_summary

router = APIRouter(prefix="/api/tournament", tags=["tournament"])

_engine = None


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


class TournamentSummary(BaseModel):
    stage: str
    matchday: int
    matchday_total: int
    teams_remaining: int
    teams_total: int
    days_to_next_phase: int | None
    next_phase_label: str | None
    group_stage_pct: int


@router.get("/summary", response_model=TournamentSummary)
def get_tournament_summary():
    session = _get_session()
    try:
        rows = session.execute(select(matches_table)).mappings().all()
    finally:
        session.close()

    matches = [
        Match(
            fixture_id=r["fixture_id"],
            group_name=r["group_name"],
            home_team=r["home_team"],
            away_team=r["away_team"],
            home_score=r["home_score"],
            away_score=r["away_score"],
            status=r["status"],
            kickoff_utc=r["kickoff_utc"],
            stage=r["stage"],
        )
        for r in rows
    ]

    by_group: dict[str, list[Match]] = defaultdict(list)
    for m in matches:
        if m.group_name:
            by_group[m.group_name].append(m)
    group_tables: dict[str, list[StandingRow]] = {
        gname: compute_group_table(gmatches)
        for gname, gmatches in by_group.items()
    }

    return TournamentSummary(**tournament_summary(matches, group_tables))
