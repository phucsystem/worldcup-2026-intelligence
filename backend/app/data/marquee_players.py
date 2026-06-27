"""Curated marquee-player snapshot — reputation-based, NOT tournament-goal based.

The top-scorers signal only surfaces players who have scored in THIS tournament, so an
elite player in a goal drought (e.g. a famous forward who hasn't scored yet) is invisible
to the model. This static map gives the forecaster a sense of each team's standout
player(s) by reputation, independent of current goal tally. Approximate pre-tournament
snapshot; teams without a clear globally-recognised standout are intentionally omitted
(absent → the signal is simply not added, never fabricated).
"""
from typing import Optional

# team name (must match DB team names verbatim) -> list of "Name — short descriptor"
_MARQUEE: dict[str, list[str]] = {
    "Argentina": ["Lionel Messi — elite forward, all-time great"],
    "Portugal": ["Cristiano Ronaldo — elite forward, all-time leading international scorer"],
    "Brazil": ["Vinícius Júnior — elite winger", "Rodrygo — top attacker"],
    "France": ["Kylian Mbappé — elite forward, world-class"],
    "Norway": ["Erling Haaland — elite striker, prolific scorer"],
    "Netherlands": ["Virgil van Dijk — world-class centre-back"],
    "England": ["Jude Bellingham — elite midfielder", "Harry Kane — prolific striker"],
    "Belgium": ["Kevin De Bruyne — world-class playmaker"],
    "Germany": ["Jamal Musiala — elite attacker", "Florian Wirtz — top playmaker"],
    "Spain": ["Lamine Yamal — elite young winger", "Rodri — Ballon d'Or midfielder"],
    "Croatia": ["Luka Modrić — world-class midfielder"],
    "Egypt": ["Mohamed Salah — elite forward, prolific scorer"],
    "Senegal": ["Sadio Mané — elite forward"],
    "South Korea": ["Son Heung-min — elite forward, captain"],
    "Morocco": ["Achraf Hakimi — elite full-back"],
    "Colombia": ["Luis Díaz — elite winger", "James Rodríguez — creative playmaker"],
    "Uruguay": ["Federico Valverde — elite midfielder", "Darwin Núñez — top striker"],
    "USA": ["Christian Pulisic — elite winger, captain"],
    "Canada": ["Alphonso Davies — elite full-back/winger"],
    "Japan": ["Takefusa Kubo — top attacker", "Kaoru Mitoma — elite winger"],
    "Mexico": ["Santiago Giménez — top striker"],
    "Switzerland": ["Granit Xhaka — experienced midfield leader"],
    "Austria": ["David Alaba — world-class defender"],
    "Ecuador": ["Moisés Caicedo — elite midfielder"],
    "Ghana": ["Mohammed Kudus — elite attacker"],
    "Scotland": ["Scott McTominay — top midfielder", "Andrew Robertson — elite full-back"],
    "Türkiye": ["Arda Güler — elite young playmaker", "Hakan Çalhanoğlu — top midfielder"],
    "Czechia": ["Patrik Schick — top striker"],
    "Paraguay": ["Miguel Almirón — top attacker"],
    "Algeria": ["Riyad Mahrez — elite winger"],
    "Bosnia & Herzegovina": ["Edin Džeko — veteran prolific striker"],
    "Iran": ["Mehdi Taremi — elite striker"],
    "New Zealand": ["Chris Wood — prolific striker"],
    "Sweden": ["Alexander Isak — elite striker"],
}


def get_marquee_players(team: str) -> Optional[list[str]]:
    """Standout player(s) for a team by reputation, or None when none is listed."""
    return _MARQUEE.get(team)
