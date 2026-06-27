"""Pure signal builders for pre-kickoff forecast enrichment.

Each builder returns a compact JSON-serializable dict or None when its source
is absent/empty. None signals are simply omitted from the facts bundle — the
'cite only provided facts' guardrail is preserved because the model only sees
what is explicitly included."""
from __future__ import annotations

from typing import Any, Optional

_FINISHED_STATUSES = {"FT", "AET", "PEN"}


def build_injury_signal(
    injuries_json: Any, team: str
) -> Optional[dict]:
    """Surface unavailable players (injuries AND suspensions) for `team` from
    the stored injuries_json blob. Both injury and suspension rows mean the
    player is unavailable — we surface both with their reason when available.

    injuries_json is expected to be {"players": [...]} where each player record
    is {player, team, reason, type}. Returns None when there is nothing to show."""
    if not injuries_json:
        return None
    if isinstance(injuries_json, dict):
        records = injuries_json.get("players") or []
    elif isinstance(injuries_json, list):
        # Tolerate a raw list shape, but treat as no-data (unexpected shape)
        return None
    else:
        return None

    unavailable = []
    seen: set[str] = set()
    for rec in records:
        if (rec.get("team") or "") != team:
            continue
        player = rec.get("player")
        if not player or player in seen:
            continue
        seen.add(player)
        unavailable.append({
            "player": player,
            "reason": rec.get("reason") or "Unavailable",
            "type": rec.get("type") or "Missing Fixture",
        })

    if not unavailable:
        return None
    return {"unavailable": unavailable}


def build_form_signal(
    finished_matches: Any, team: str
) -> Optional[dict]:
    """Recent match form for `team` from a list of finished match dicts.

    Each match dict is expected to carry home_team, away_team, home_score,
    away_score. Returns None when there are no finished matches."""
    if not finished_matches:
        return None

    form = []
    for m in finished_matches:
        home = m.get("home_team")
        away = m.get("away_team")
        hs = m.get("home_score")
        as_ = m.get("away_score")
        if hs is None or as_ is None:
            continue
        if home == team:
            gf, ga = hs, as_
        elif away == team:
            gf, ga = as_, hs
        else:
            continue
        if gf > ga:
            result = "W"
        elif gf == ga:
            result = "D"
        else:
            result = "L"
        form.append({"result": result, "gf": gf, "ga": ga})

    if not form:
        return None
    return {"form": form}


def build_strength_signal(
    team: str,
    *,
    fifa_rank: Optional[int],
    standing_row,
    top_scorers: list,
    marquee_players: Optional[list] = None,
) -> Optional[dict]:
    """Composite strength signal: FIFA rank + strike rate + top scorers + marquee players.

    `standing_row` is a StandingRow or None; `top_scorers` is a list of TopScorer
    objects for this team; `marquee_players` is a reputation-based standout list
    (independent of tournament goals, so it surfaces elite players who haven't scored).
    Returns None when there is truly nothing to say."""
    signal: dict = {}

    if fifa_rank is not None:
        signal["fifa_rank"] = fifa_rank

    if marquee_players:
        signal["marquee_players"] = list(marquee_players)

    if standing_row is not None:
        played = getattr(standing_row, "played", None) or 0
        gf = getattr(standing_row, "gf", None) or 0
        if played > 0:
            signal["goals_per_game"] = round(gf / played, 2)

    scorers = [
        {"name": ts.name, "goals": ts.goals}
        for ts in (top_scorers or [])
        if ts.goals > 0
    ]
    if scorers:
        signal["top_scorers"] = scorers

    if not signal:
        return None
    return signal
