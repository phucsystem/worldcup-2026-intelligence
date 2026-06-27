"""TDD tests for GET /api/forecast/accuracy.

Seeded matches with known outcomes let us hand-verify every metric before
the endpoint exists — run first to confirm red, then green after implementation.

Notation for the seed set (5 matches):
  M1: Brazil 3-1 Serbia  forecast=H(60)/D(25)/A(15)  → argmax=H, actual=H → HIT
  M2: France 0-2 Poland  forecast=H(20)/D(15)/A(65)  → argmax=A, actual=A → HIT
  M3: Spain  1-1 Germany forecast=H(40)/D(30)/A(30)  → argmax=H, actual=D → MISS
  M4: USA    0-1 Mexico  forecast=H(55)/D(25)/A(20)  → argmax=H, actual=A → MISS
  M5: (no forecast_json)  → excluded from scope

Derived by hand:
  total=4, hits=2, accuracy_pct=50.0
  brier: per match = sum of 3 squared differences (prob as fraction of 100)
    M1: (0.60-1)^2 + (0.25-0)^2 + (0.15-0)^2 = 0.1600+0.0625+0.0225 = 0.2450
    M2: (0.20-0)^2 + (0.15-0)^2 + (0.65-1)^2 = 0.0400+0.0225+0.1225 = 0.1850
    M3: (0.40-0)^2 + (0.30-1)^2 + (0.30-0)^2 = 0.1600+0.4900+0.0900 = 0.7400
    M4: (0.55-0)^2 + (0.25-0)^2 + (0.20-1)^2 = 0.3025+0.0625+0.6400 = 1.0050
    mean = (0.2450+0.1850+0.7400+1.0050)/4 = 2.175/4 = 0.54375 → rounded 4dp = 0.5438

  draw stats:
    draw_actual    = matches where actual==draw = M3 only → 1
    draw_predicted = matches where argmax==draw = 0 (none have draw as argmax)
    draw_hits      = matches where actual==draw AND argmax==draw = 0
    draw_recall    = draw_hits/draw_actual = 0/1 = 0.0
    draw_precision = None (draw_predicted==0 → denominator 0)
"""

import json
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.repository import matches_table


# ---------------------------------------------------------------------------
# Shared seed helpers
# ---------------------------------------------------------------------------

def _dt(y, m, d):
    return datetime(y, m, d, 12, 0, tzinfo=timezone.utc)


def _fc(h, d, a):
    return {"home_pct": h, "draw_pct": d, "away_pct": a}


_SEED_MATCHES = [
    # M1: Brazil wins, forecast=home → HIT
    {
        "fixture_id": 101, "home_team": "Brazil", "away_team": "Serbia",
        "home_score": 3, "away_score": 1, "status": "FT",
        "kickoff_utc": _dt(2026, 6, 12), "group_name": "G", "stage": "Group Stage",
        "forecast_json": _fc(60, 25, 15),
    },
    # M2: Poland wins away, forecast=away (argmax A=65) → HIT
    {
        "fixture_id": 102, "home_team": "France", "away_team": "Poland",
        "home_score": 0, "away_score": 2, "status": "FT",
        "kickoff_utc": _dt(2026, 6, 13), "group_name": "C", "stage": "Group Stage",
        "forecast_json": _fc(20, 15, 65),
    },
    # M3: Draw, forecast=home (argmax 40) → MISS
    {
        "fixture_id": 103, "home_team": "Spain", "away_team": "Germany",
        "home_score": 1, "away_score": 1, "status": "AET",
        "kickoff_utc": _dt(2026, 6, 14), "group_name": "E", "stage": "Group Stage",
        "forecast_json": _fc(40, 30, 30),
    },
    # M4: Mexico wins, forecast=home → MISS
    {
        "fixture_id": 104, "home_team": "USA", "away_team": "Mexico",
        "home_score": 0, "away_score": 1, "status": "PEN",
        "kickoff_utc": _dt(2026, 6, 15), "group_name": None, "stage": "Round of 16",
        "forecast_json": _fc(55, 25, 20),
    },
    # M5: no forecast → excluded from accuracy scope
    {
        "fixture_id": 105, "home_team": "Italy", "away_team": "Japan",
        "home_score": 2, "away_score": 0, "status": "FT",
        "kickoff_utc": _dt(2026, 6, 16), "group_name": "F", "stage": "Group Stage",
        "forecast_json": None,
    },
]


@pytest.fixture()
def db_session():
    """In-memory SQLite with the matches schema, seeded with known data."""
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    matches_table.create(bind=engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    for row in _SEED_MATCHES:
        session.execute(matches_table.insert().values(**row))
    session.commit()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Pure computation tests (no DB, no HTTP)
# ---------------------------------------------------------------------------

class TestForecastAccuracyPure:
    """Test the pure compute function before the HTTP layer."""

    def test_hit_count_and_accuracy(self, db_session):
        from app.api.forecast_accuracy import compute_accuracy

        result = compute_accuracy(db_session)
        assert result.total == 4        # M5 excluded (no forecast)
        assert result.hits == 2         # M1 (H→H) and M2 (A→A)
        assert result.accuracy_pct == 50.0

    def test_brier_score(self, db_session):
        from app.api.forecast_accuracy import compute_accuracy

        result = compute_accuracy(db_session)
        # Hand-computed: 0.5438 (see module docstring)
        assert result.brier == pytest.approx(0.5438, abs=0.0001)

    def test_draw_stats(self, db_session):
        from app.api.forecast_accuracy import compute_accuracy

        result = compute_accuracy(db_session)
        assert result.draw_actual == 1      # only M3
        assert result.draw_predicted == 0   # no match has draw as argmax
        assert result.draw_hits == 0
        assert result.draw_recall == pytest.approx(0.0)
        assert result.draw_precision is None  # denominator 0

    def test_stage_filter_group_only(self, db_session):
        from app.api.forecast_accuracy import compute_accuracy

        # stage=group excludes M4 (group_name IS NULL)
        result = compute_accuracy(db_session, stage="group")
        assert result.total == 3  # M1, M2, M3 (M5 has no forecast, M4 is KO)

    def test_stage_filter_ko_only(self, db_session):
        from app.api.forecast_accuracy import compute_accuracy

        result = compute_accuracy(db_session, stage="ko")
        assert result.total == 1  # only M4 (knockout + has forecast)

    def test_empty_scope_returns_zeros(self, db_session):
        from app.api.forecast_accuracy import compute_accuracy

        # days=0 → no matches in the last 0 days (empty scope)
        result = compute_accuracy(db_session, days=0)
        assert result.total == 0
        assert result.hits == 0
        assert result.accuracy_pct == 0.0
        assert result.brier is None
        assert result.draw_precision is None
        assert result.draw_recall is None


# ---------------------------------------------------------------------------
# HTTP endpoint tests
# ---------------------------------------------------------------------------

class TestForecastAccuracyEndpoint:
    """Patch _get_session to inject the seeded in-memory DB."""

    def _make_client(self, session):
        import app.api.forecast_accuracy as fa_module
        from fastapi.testclient import TestClient
        from app.main import app

        original = fa_module._get_session

        def _override():
            return session

        fa_module._get_session = _override
        client = TestClient(app)
        try:
            yield client
        finally:
            fa_module._get_session = original

    def test_returns_200_with_correct_total(self, db_session):
        import app.api.forecast_accuracy as fa_module
        from fastapi.testclient import TestClient
        from app.main import app

        original = fa_module._get_session
        fa_module._get_session = lambda: db_session
        try:
            client = TestClient(app)
            resp = client.get("/api/forecast/accuracy")
            assert resp.status_code == 200
            body = resp.json()
            assert body["total"] == 4
            assert body["hits"] == 2
            assert body["accuracy_pct"] == 50.0
        finally:
            fa_module._get_session = original

    def test_empty_scope_200_not_crash(self, db_session):
        import app.api.forecast_accuracy as fa_module
        from fastapi.testclient import TestClient
        from app.main import app

        original = fa_module._get_session
        fa_module._get_session = lambda: db_session
        try:
            client = TestClient(app)
            resp = client.get("/api/forecast/accuracy?days=0")
            assert resp.status_code == 200
            body = resp.json()
            assert body["total"] == 0
            assert body["brier"] is None
        finally:
            fa_module._get_session = original

    def test_stage_group_filter(self, db_session):
        import app.api.forecast_accuracy as fa_module
        from fastapi.testclient import TestClient
        from app.main import app

        original = fa_module._get_session
        fa_module._get_session = lambda: db_session
        try:
            client = TestClient(app)
            resp = client.get("/api/forecast/accuracy?stage=group")
            assert resp.status_code == 200
            assert resp.json()["total"] == 3
        finally:
            fa_module._get_session = original

    def test_invalid_stage_422(self, db_session):
        import app.api.forecast_accuracy as fa_module
        from fastapi.testclient import TestClient
        from app.main import app

        original = fa_module._get_session
        fa_module._get_session = lambda: db_session
        try:
            client = TestClient(app)
            resp = client.get("/api/forecast/accuracy?stage=bogus")
            assert resp.status_code == 422
        finally:
            fa_module._get_session = original
