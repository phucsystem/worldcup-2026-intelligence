from __future__ import annotations

from typing import Any, Optional, TypedDict


class BriefState(TypedDict):
    brief_date: str  # ISO date string YYYY-MM-DD
    matches: list[dict]
    standings: list[dict]
    # computed_facts keys (built by collector_node): brief_date,
    # total_matches_completed/upcoming, completed_results, upcoming_fixtures
    # (each carries fixture_id), group_tables, best_third_place_teams,
    # qualification_status, and stake_groups (contention groups w/ deterministic
    # per-team scenario rows — the analyst narrates these).
    computed_facts: dict[str, Any]
    intelligence: dict[str, Any]
    article: dict[str, Any]
    run_id: str
    node_timings: dict[str, float]
    tokens_in: int
    tokens_out: int
    cost_usd: float
    error: Optional[str]
