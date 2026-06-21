"""
Phase 2 tests: analyst structured-output shape (mocked client), intelligence
merge (pure), and the tournament-summary endpoint.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.nodes_analyst import Intelligence, analyst_node
from app.pipeline.run import merge_intelligence

client = TestClient(app)


# ---------------------------------------------------------------------------
# Intelligence schema + analyst node
# ---------------------------------------------------------------------------

def test_intelligence_model_dump_includes_new_fields():
    intel = Intelligence(
        storylines=[], surprise_teams=[], underperformers=[],
        power_ranking=[], qualification_narrative="",
    )
    dumped = intel.model_dump()
    assert dumped["fixture_stakes"] == []
    assert dumped["group_scenarios"] == []


def test_analyst_node_emits_new_fields(monkeypatch):
    fake = Intelligence(
        storylines=["s"], surprise_teams=[], underperformers=[],
        power_ranking=[], qualification_narrative="q",
        fixture_stakes=[{"fixture_id": 42, "stake_text": "win to top group"}],
        group_scenarios=[{"group_name": "Group A", "tag": "Tomorrow", "line": "tight"}],
    )

    class FakeClient:
        def invoke(self, messages):
            return {"parsed": fake, "raw": None}

    monkeypatch.setattr(
        "app.llm.deepseek.make_structured_client", lambda schema: FakeClient()
    )

    state = {
        "brief_date": "2026-06-20",
        "computed_facts": {"upcoming_fixtures": [], "stake_groups": []},
        "node_timings": {},
        "tokens_in": 0,
        "tokens_out": 0,
    }
    out = analyst_node(state)
    intel = out["intelligence"]
    assert intel["fixture_stakes"][0]["fixture_id"] == 42
    assert intel["group_scenarios"][0]["group_name"] == "Group A"


# ---------------------------------------------------------------------------
# merge_intelligence
# ---------------------------------------------------------------------------

def test_merge_attaches_rows_and_drops_unmatched():
    intel = {"group_scenarios": [
        {"group_name": "Group A", "tag": "t", "line": "l"},
        {"group_name": "Group Z", "tag": "t", "line": "l"},  # no deterministic rows
    ]}
    stake_groups = [
        {"group_name": "Group A", "rows": [{"team": "A1", "note": "Through"}]},
    ]
    out = merge_intelligence(intel, stake_groups)
    names = [s["group_name"] for s in out["group_scenarios"]]
    assert names == ["Group A"]
    assert out["group_scenarios"][0]["rows"][0]["team"] == "A1"


def test_merge_handles_missing_keys():
    assert merge_intelligence(None, None)["group_scenarios"] == []
    assert merge_intelligence({}, [])["group_scenarios"] == []


# ---------------------------------------------------------------------------
# tournament summary endpoint
# ---------------------------------------------------------------------------

def test_tournament_summary_endpoint_keys():
    r = client.get("/api/tournament/summary")
    assert r.status_code == 200
    data = r.json()
    for key in (
        "stage", "matchday", "matchday_total", "teams_remaining",
        "teams_total", "days_to_next_phase", "next_phase_label", "group_stage_pct",
    ):
        assert key in data
    assert data["teams_total"] == 48
