"""TDD tests for Slice 3 signal builders and FIFA ranking lookup.

No DB, no network, no LLM — all builders are pure functions.
"""
from app.data.fifa_rankings import get_fifa_rank
from app.pipeline.forecast_signals import (
    build_injury_signal,
    build_form_signal,
    build_strength_signal,
)
from app.data.models import StandingRow


# ── FIFA ranking ─────────────────────────────────────────────────────────────

class TestGetFifaRank:
    def test_known_team_returns_int(self):
        rank = get_fifa_rank("Spain")
        assert isinstance(rank, int)
        assert rank >= 1

    def test_strong_teams_rank_higher_than_weak(self):
        # Lower number = better rank
        assert get_fifa_rank("Argentina") < get_fifa_rank("Haiti")
        assert get_fifa_rank("France") < get_fifa_rank("Curaçao")

    def test_unknown_team_returns_none(self):
        assert get_fifa_rank("Atlantis FC") is None
        assert get_fifa_rank("") is None

    def test_all_48_teams_covered(self):
        teams = [
            "Algeria", "Argentina", "Australia", "Austria", "Belgium",
            "Bosnia & Herzegovina", "Brazil", "Canada", "Cape Verde Islands",
            "Colombia", "Congo DR", "Croatia", "Curaçao", "Czechia",
            "Ecuador", "Egypt", "England", "France", "Germany", "Ghana",
            "Haiti", "Iran", "Iraq", "Ivory Coast", "Japan", "Jordan",
            "Mexico", "Morocco", "Netherlands", "New Zealand", "Norway",
            "Panama", "Paraguay", "Portugal", "Qatar", "Saudi Arabia",
            "Scotland", "Senegal", "South Africa", "South Korea", "Spain",
            "Sweden", "Switzerland", "Tunisia", "Türkiye", "USA", "Uruguay",
            "Uzbekistan",
        ]
        for team in teams:
            rank = get_fifa_rank(team)
            assert isinstance(rank, int), f"{team!r} missing from rankings"


# ── Injury signal ─────────────────────────────────────────────────────────────

class TestBuildInjurySignal:
    def _records(self):
        return [
            {"player": "Araujo", "team": "Uruguay", "reason": "Hamstring", "type": "Missing Fixture"},
            {"player": "Valverde", "team": "Uruguay", "reason": "Red Card", "type": "Missing Fixture"},
            {"player": "Gomez", "team": "Argentina", "reason": "Knee", "type": "Missing Fixture"},
            {"player": "Dybala", "team": "Uruguay", "reason": "Doubtful", "type": "Questionable"},
        ]

    def test_both_injuries_and_suspensions_surfaced(self):
        sig = build_injury_signal({"players": self._records()}, "Uruguay")
        assert sig is not None
        names = [p["player"] for p in sig["unavailable"]]
        # Araujo is an injury, Valverde is a suspension — both unavailable
        assert "Araujo" in names
        assert "Valverde" in names

    def test_only_own_team_included(self):
        sig = build_injury_signal({"players": self._records()}, "Uruguay")
        names = [p["player"] for p in sig["unavailable"]]
        assert "Gomez" not in names  # Argentina's player

    def test_reason_preserved_when_available(self):
        sig = build_injury_signal({"players": self._records()}, "Uruguay")
        araujo = next(p for p in sig["unavailable"] if p["player"] == "Araujo")
        assert araujo["reason"] == "Hamstring"

    def test_empty_players_returns_none(self):
        assert build_injury_signal({"players": []}, "Uruguay") is None

    def test_missing_injuries_json_returns_none(self):
        assert build_injury_signal(None, "Uruguay") is None

    def test_injuries_json_without_players_key_returns_none(self):
        assert build_injury_signal({}, "Uruguay") is None

    def test_list_form_injuries_json_tolerated(self):
        # Raw list (no wrapper dict) — should still work or return None gracefully
        result = build_injury_signal(
            [{"player": "Araujo", "team": "Uruguay", "reason": "Hamstring", "type": "Missing Fixture"}],
            "Uruguay",
        )
        # Either surfaces the player or returns None — must not crash
        assert result is None or "unavailable" in result


# ── Form signal ───────────────────────────────────────────────────────────────

class TestBuildFormSignal:
    def _finished_matches(self):
        return [
            {"status": "FT", "home_team": "Brazil", "away_team": "Serbia",
             "home_score": 2, "away_score": 0},
            {"status": "FT", "home_team": "Switzerland", "away_team": "Brazil",
             "home_score": 0, "away_score": 1},
            {"status": "FT", "home_team": "Brazil", "away_team": "Germany",
             "home_score": 1, "away_score": 1},
        ]

    def test_returns_form_string_for_team(self):
        sig = build_form_signal(self._finished_matches(), "Brazil")
        assert sig is not None
        assert "form" in sig
        # 3 matches → 3 entries: W, W, D
        assert len(sig["form"]) == 3

    def test_win_draw_loss_correctly_labelled(self):
        sig = build_form_signal(self._finished_matches(), "Brazil")
        results = [entry["result"] for entry in sig["form"]]
        assert results == ["W", "W", "D"]

    def test_goals_for_against_per_match(self):
        sig = build_form_signal(self._finished_matches(), "Brazil")
        first = sig["form"][0]
        assert first["gf"] == 2
        assert first["ga"] == 0

    def test_no_finished_matches_returns_none(self):
        assert build_form_signal([], "Brazil") is None

    def test_none_matches_returns_none(self):
        assert build_form_signal(None, "Brazil") is None


# ── Strength signal ────────────────────────────────────────────────────────────

class TestBuildStrengthSignal:
    def _row(self):
        return StandingRow(
            group_name="G", team="Brazil", position=1, points=9,
            played=3, won=3, drawn=0, lost=0, gf=7, ga=1, gd=6,
        )

    def _scorers(self):
        # TopScorer-like dicts
        from app.data.models import TopScorer
        return [
            TopScorer(player_id=1, name="Richarlison", team="Brazil", goals=3),
            TopScorer(player_id=2, name="Vinicius Jr", team="Brazil", goals=2),
        ]

    def test_returns_goals_per_game(self):
        sig = build_strength_signal("Brazil", fifa_rank=5, standing_row=self._row(), top_scorers=self._scorers())
        assert sig is not None
        assert abs(sig["goals_per_game"] - 7 / 3) < 0.01

    def test_includes_fifa_rank(self):
        sig = build_strength_signal("Brazil", fifa_rank=5, standing_row=self._row(), top_scorers=self._scorers())
        assert sig["fifa_rank"] == 5

    def test_top_scorers_listed(self):
        sig = build_strength_signal("Brazil", fifa_rank=5, standing_row=self._row(), top_scorers=self._scorers())
        assert len(sig["top_scorers"]) == 2
        assert sig["top_scorers"][0]["name"] == "Richarlison"
        assert sig["top_scorers"][0]["goals"] == 3

    def test_no_standing_row_still_works_with_rank_only(self):
        sig = build_strength_signal("Brazil", fifa_rank=5, standing_row=None, top_scorers=[])
        assert sig is not None
        assert sig["fifa_rank"] == 5
        assert "goals_per_game" not in sig or sig.get("goals_per_game") is None

    def test_no_rank_no_row_no_scorers_returns_none(self):
        sig = build_strength_signal("Atlantis FC", fifa_rank=None, standing_row=None, top_scorers=[])
        assert sig is None

    def test_rank_alone_sufficient(self):
        sig = build_strength_signal("Brazil", fifa_rank=5, standing_row=None, top_scorers=[])
        assert sig is not None

    def test_marquee_players_listed(self):
        sig = build_strength_signal(
            "Portugal", fifa_rank=6, standing_row=None, top_scorers=[],
            marquee_players=["Cristiano Ronaldo — elite forward"],
        )
        assert sig["marquee_players"] == ["Cristiano Ronaldo — elite forward"]

    def test_marquee_alone_sufficient(self):
        # A famous-but-not-top-scoring player still produces a signal with no other data.
        sig = build_strength_signal(
            "Portugal", fifa_rank=None, standing_row=None, top_scorers=[],
            marquee_players=["Cristiano Ronaldo — elite forward"],
        )
        assert sig is not None and "marquee_players" in sig

    def test_marquee_absent_when_none(self):
        sig = build_strength_signal(
            "Brazil", fifa_rank=5, standing_row=None, top_scorers=[], marquee_players=None,
        )
        assert "marquee_players" not in sig


class TestMarqueePlayers:
    def test_known_team(self):
        from app.data.marquee_players import get_marquee_players
        out = get_marquee_players("Portugal")
        assert out and any("Ronaldo" in p for p in out)

    def test_unknown_team_none(self):
        from app.data.marquee_players import get_marquee_players
        assert get_marquee_players("Atlantis FC") is None


# ── Facts builders — signals integration ──────────────────────────────────────

class TestForecastFactsWithSignals:
    def _rows(self):
        return [
            StandingRow(group_name="G", team="Brazil", points=9, position=1,
                        played=3, won=3, gf=7, ga=1, gd=6, qualification="qualified"),
            StandingRow(group_name="G", team="Serbia", points=3, position=3,
                        played=3, won=1, gf=2, ga=4, gd=-2, qualification="contention"),
        ]

    def test_group_facts_with_signals_includes_signals_key(self):
        from app.pipeline.forecast import build_match_forecast_facts
        rows = self._rows()
        home_row = rows[0]
        away_row = rows[1]
        signals = {"home": {"fifa_rank": 5}, "away": {"fifa_rank": 43}}
        facts = build_match_forecast_facts(
            home_team="Brazil", away_team="Serbia",
            home_row=home_row, away_row=away_row,
            group_name="G", signals=signals,
        )
        assert facts is not None
        assert "signals" in facts
        assert facts["signals"]["home"]["fifa_rank"] == 5

    def test_group_facts_without_signals_omits_key(self):
        from app.pipeline.forecast import build_match_forecast_facts
        rows = self._rows()
        facts = build_match_forecast_facts(
            home_team="Brazil", away_team="Serbia",
            home_row=rows[0], away_row=rows[1],
            group_name="G",
        )
        assert facts is not None
        assert "signals" not in facts

    def test_ko_facts_with_signals_includes_signals_key(self):
        from app.pipeline.forecast import build_ko_forecast_facts
        rows = self._rows()
        signals = {"home": {"form": [{"result": "W"}]}, "away": {}}
        facts = build_ko_forecast_facts(
            home_team="Brazil", away_team="Serbia",
            home_row=rows[0], away_row=rows[1],
            signals=signals,
        )
        assert facts is not None
        assert "signals" in facts

    def test_ko_facts_without_signals_omits_key(self):
        from app.pipeline.forecast import build_ko_forecast_facts
        rows = self._rows()
        facts = build_ko_forecast_facts(
            home_team="Brazil", away_team="Serbia",
            home_row=rows[0], away_row=rows[1],
        )
        assert "signals" not in facts


# ── Prompt draw guidance ──────────────────────────────────────────────────────

class TestForecastPromptDrawGuidance:
    def test_group_prompt_contains_draw_base_rate(self):
        from app.pipeline.prompts import FORECAST_SYSTEM
        # The prompt must tell the model the observed draw base rate
        text = FORECAST_SYSTEM.lower()
        assert "draw" in text
        assert any(token in text for token in ["25", "28", "base rate", "base-rate", "observed"])

    def test_group_prompt_references_signals_when_present(self):
        from app.pipeline.prompts import FORECAST_SYSTEM
        assert "signal" in FORECAST_SYSTEM.lower()
