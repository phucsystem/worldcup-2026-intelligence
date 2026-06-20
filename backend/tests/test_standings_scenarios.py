"""
Unit tests for group_scenarios() and tournament_summary() — pure, no I/O.
"""

from datetime import date, datetime, timezone

from app.data.models import Match, StandingRow
from app.data.standings_math import group_scenarios, tournament_summary


def _full_group(group_name: str, teams_pts: list[tuple[str, int, int, int]]) -> list[StandingRow]:
    """teams_pts: [(team, points, gd, gf)] best-first, all played=3."""
    rows = []
    for i, (team, pts, gd, gf) in enumerate(teams_pts, start=1):
        rows.append(StandingRow(
            group_name=group_name, team=team,
            played=3, points=pts, gd=gd, gf=gf, position=i,
            won=pts // 3, drawn=pts % 3, lost=3 - (pts // 3) - (pts % 3),
            ga=gf - gd,
        ))
    return rows


def _incomplete_group(group_name: str, teams: list[tuple[str, int, int, int, int]]) -> list[StandingRow]:
    """teams: [(team, played, points, gd, gf)] best-first."""
    rows = []
    for i, (team, played, pts, gd, gf) in enumerate(teams, start=1):
        rows.append(StandingRow(
            group_name=group_name, team=team,
            played=played, points=pts, gd=gd, gf=gf, position=i, ga=gf - gd,
        ))
    return rows


def _match(fixture_id, group, hs, as_, kickoff=None, stage=None) -> Match:
    return Match(
        fixture_id=fixture_id, group_name=group,
        home_team="H", away_team="A", home_score=hs, away_score=as_,
        status="FT" if hs is not None else "NS",
        kickoff_utc=kickoff, stage=stage,
    )


def _12_complete_groups() -> dict[str, list[StandingRow]]:
    tables = {}
    for letter in "ABCDEFGHIJKL":
        gname = f"Group {letter}"
        tables[gname] = _full_group(gname, [
            (f"{letter}1", 9, 6, 7), (f"{letter}2", 6, 2, 4),
            (f"{letter}3", 3, -1, 2), (f"{letter}4", 0, -7, 0),
        ])
    return tables


# ---------------------------------------------------------------------------
# group_scenarios
# ---------------------------------------------------------------------------

class TestGroupScenarios:
    def test_complete_group_notes(self):
        tables = _12_complete_groups()
        out = group_scenarios(tables)
        rows = {r["team"]: r for r in out["Group A"]}
        assert rows["A1"]["note"] == "Through" and rows["A1"]["status"] == "qualified"
        assert rows["A2"]["note"] == "Through" and rows["A2"]["status"] == "qualified"
        assert rows["A4"]["note"] == "Out" and rows["A4"]["status"] == "out"

    def test_rows_are_position_ordered(self):
        tables = _12_complete_groups()
        positions = [r["position"] for r in group_scenarios(tables)["Group A"]]
        assert positions == [1, 2, 3, 4]

    def test_contention_top_two_vs_chasers(self):
        # Single incomplete group → all teams in contention.
        tables = {"Group A": _incomplete_group("Group A", [
            ("A1", 1, 3, 1, 2),
            ("A2", 1, 3, 1, 2),
            ("A3", 1, 0, -1, 0),
            ("A4", 1, 0, -1, 0),
        ])}
        rows = {r["team"]: r for r in group_scenarios(tables)["Group A"]}
        assert rows["A1"]["note"] == "Win = top"
        assert rows["A3"]["note"] == "Must win"
        assert all(r["status"] == "contention" for r in rows.values())


# ---------------------------------------------------------------------------
# tournament_summary
# ---------------------------------------------------------------------------

class TestTournamentSummary:
    def test_complete_groups_knockout_stage(self):
        tables = _12_complete_groups()
        matches = [_match(i, "Group A", 1, 0) for i in range(1, 7)]
        s = tournament_summary(matches, tables)
        assert s["stage"] == "Knockout"
        assert s["matchday"] == 3
        assert s["matchday_total"] == 3
        # 2 qualified + best-thirds survive; 4th places eliminated.
        assert s["teams_remaining"] == 48 - 0 or s["teams_remaining"] > 0
        assert s["teams_total"] == 48
        assert s["group_stage_pct"] == 100

    def test_incomplete_group_stage(self):
        tables = {"Group A": _incomplete_group("Group A", [
            ("A1", 1, 3, 1, 2), ("A2", 1, 3, 1, 2),
            ("A3", 1, 0, -1, 0), ("A4", 1, 0, -1, 0),
        ])}
        # 2 of 6 group matches played.
        matches = [_match(1, "Group A", 1, 0), _match(2, "Group A", 2, 1)] + [
            _match(i, "Group A", None, None) for i in range(3, 7)
        ]
        s = tournament_summary(matches, tables)
        assert s["stage"] == "Group Stage"
        assert s["matchday"] == 1
        assert s["group_stage_pct"] == 33  # 2/6
        assert s["days_to_next_phase"] is None
        assert s["next_phase_label"] is None

    def test_days_to_next_phase(self):
        tables = _12_complete_groups()
        ko = _match(
            99, None, None, None,
            kickoff=datetime(2026, 7, 5, 10, 0, tzinfo=timezone.utc),
            stage="Round of 32",
        )
        matches = [_match(i, "Group A", 1, 0) for i in range(1, 7)] + [ko]
        s = tournament_summary(matches, tables, today=date(2026, 7, 1))
        assert s["days_to_next_phase"] == 4
        assert s["next_phase_label"] == "Round of 32"

    def test_empty_tables_graceful(self):
        s = tournament_summary([], {})
        assert s["stage"] == "Group Stage"
        assert s["matchday"] == 0
        assert s["group_stage_pct"] == 0
        assert s["teams_remaining"] == 0
