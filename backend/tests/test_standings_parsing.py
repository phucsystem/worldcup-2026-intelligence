"""
Unit tests for parse_teams_from_standings — pure, no network.

Locks the WC-2026 regression: the /standings payload carries 12 real group
blocks (A–L) PLUS an aggregate "Group Stage" block repeating many teams. The
aggregate must never overwrite a team's real group, regardless of block order.
"""

from app.data.api_football import parse_teams_from_standings


def _entry(team_id, name, group):
    return {"team": {"id": team_id, "name": name, "logo": f"logo/{team_id}.png"}, "group": group}


def _payload(*blocks):
    return {"response": [{"league": {"standings": list(blocks)}}]}


def _by_name(teams):
    return {t.name: t for t in teams}


class TestParseTeamsFromStandings:
    def test_aggregate_block_does_not_overwrite_real_group(self):
        # Brazil appears in real "Group C" AND the trailing aggregate "Group Stage".
        payload = _payload(
            [_entry(1, "Brazil", "Group C"), _entry(2, "Scotland", "Group C")],
            [_entry(1, "Brazil", "Group Stage"), _entry(3, "Spain", "Group Stage")],
        )
        teams = _by_name(parse_teams_from_standings(payload))
        assert teams["Brazil"].group_name == "Group C"
        # A team seen only in the aggregate keeps no bogus group label.
        assert teams["Spain"].group_name is None

    def test_real_group_wins_even_if_aggregate_comes_first(self):
        payload = _payload(
            [_entry(1, "Brazil", "Group Stage")],  # aggregate first
            [_entry(1, "Brazil", "Group C")],       # real group second
        )
        teams = _by_name(parse_teams_from_standings(payload))
        assert teams["Brazil"].group_name == "Group C"

    def test_no_duplicate_team_rows(self):
        payload = _payload(
            [_entry(1, "Brazil", "Group C")],
            [_entry(1, "Brazil", "Group Stage")],
        )
        teams = parse_teams_from_standings(payload)
        assert len([t for t in teams if t.name == "Brazil"]) == 1

    def test_logo_captured_from_first_seen(self):
        teams = _by_name(parse_teams_from_standings(_payload([_entry(7, "France", "Group I")])))
        assert teams["France"].logo_url == "logo/7.png"

    def test_skips_entries_missing_id_or_name(self):
        payload = _payload([
            {"team": {"name": "NoId"}, "group": "Group A"},
            {"team": {"id": 9}, "group": "Group A"},
        ])
        assert parse_teams_from_standings(payload) == []

    def test_twelve_groups_of_four_plus_aggregate(self):
        # 12 groups × 4 teams = 48 unique; aggregate repeats 12 of them.
        groups = [chr(ord("A") + i) for i in range(12)]
        real_blocks = [
            [_entry(g_i * 4 + j, f"T{g_i*4+j}", f"Group {g}") for j in range(4)]
            for g_i, g in enumerate(groups)
        ]
        aggregate = [[_entry(i, f"T{i}", "Group Stage") for i in range(12)]]
        teams = parse_teams_from_standings(_payload(*real_blocks, *aggregate))
        assert len(teams) == 48
        assert all(t.group_name in {f"Group {g}" for g in groups} for t in teams)
