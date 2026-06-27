"""Read-only endpoint: GET /api/forecast/accuracy

Computes forecast quality metrics over all finished matches that carry a
forecast_json blob. Useful for evaluating model changes over time.
"""
import json as _json
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.api.standings import forecast_correct
from app.data.repository import make_engine, make_session_factory, matches_table

router = APIRouter(prefix="/api/forecast", tags=["forecast"])

# Mirror of standings._FINISHED — duplication accepted over coupling the API
# layers together (see repository.py comment for precedent).
_FINISHED = {"FT", "AET", "PEN"}

_engine = None


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


class ForecastAccuracy(BaseModel):
    total: int
    hits: int
    accuracy_pct: float
    brier: Optional[float]
    draw_actual: int
    draw_predicted: int
    draw_hits: int
    draw_precision: Optional[float]
    draw_recall: Optional[float]


def compute_accuracy(
    session,
    days: Optional[int] = None,
    stage: Optional[Literal["group", "ko"]] = None,
) -> ForecastAccuracy:
    """Pure computation over a session; returns zero-filled result on empty scope."""
    stmt = select(matches_table).where(
        matches_table.c.status.in_(_FINISHED),
        matches_table.c.forecast_json.isnot(None),
    )
    if days is not None:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        stmt = stmt.where(matches_table.c.kickoff_utc >= cutoff)
    if stage == "group":
        stmt = stmt.where(matches_table.c.group_name.isnot(None))
    elif stage == "ko":
        stmt = stmt.where(matches_table.c.group_name.is_(None))

    rows = session.execute(stmt).mappings().all()

    total = 0
    hits = 0
    brier_sum = 0.0
    draw_actual = 0
    draw_predicted = 0
    draw_hits = 0

    for r in rows:
        fc = r["forecast_json"]
        hs = r["home_score"]
        as_ = r["away_score"]
        if hs is None or as_ is None:
            continue
        # SQLite returns JSON columns as strings; PostgreSQL returns dicts.
        if isinstance(fc, str):
            try:
                fc = _json.loads(fc)
            except Exception:
                fc = None
        if not fc:
            continue

        total += 1

        h = (fc.get("home_pct") or 0) / 100.0
        d = (fc.get("draw_pct") or 0) / 100.0
        a = (fc.get("away_pct") or 0) / 100.0

        actual = "home" if hs > as_ else "away" if hs < as_ else "draw"
        oh = 1.0 if actual == "home" else 0.0
        od = 1.0 if actual == "draw" else 0.0
        oa = 1.0 if actual == "away" else 0.0
        brier_sum += (h - oh) ** 2 + (d - od) ** 2 + (a - oa) ** 2

        if forecast_correct(fc, hs, as_):
            hits += 1

        # argmax needed separately to count draw_predicted (forecast_correct returns bool only)
        if h >= d and h >= a:
            predicted = "home"
        elif a >= d:
            predicted = "away"
        else:
            predicted = "draw"

        if actual == "draw":
            draw_actual += 1
        if predicted == "draw":
            draw_predicted += 1
        if actual == "draw" and predicted == "draw":
            draw_hits += 1

    if total == 0:
        return ForecastAccuracy(
            total=0, hits=0, accuracy_pct=0.0, brier=None,
            draw_actual=0, draw_predicted=0, draw_hits=0,
            draw_precision=None, draw_recall=None,
        )

    accuracy_pct = round(hits / total * 100, 1)
    brier = round(brier_sum / total, 4)
    draw_precision = round(draw_hits / draw_predicted, 4) if draw_predicted else None
    draw_recall = round(draw_hits / draw_actual, 4) if draw_actual else None

    return ForecastAccuracy(
        total=total,
        hits=hits,
        accuracy_pct=accuracy_pct,
        brier=brier,
        draw_actual=draw_actual,
        draw_predicted=draw_predicted,
        draw_hits=draw_hits,
        draw_precision=draw_precision,
        draw_recall=draw_recall,
    )


@router.get("/accuracy", response_model=ForecastAccuracy)
def get_forecast_accuracy(
    days: Optional[int] = Query(default=None, ge=0),
    stage: Optional[Literal["group", "ko"]] = Query(default=None),
):
    session = _get_session()
    try:
        return compute_accuracy(session, days=days, stage=stage)
    finally:
        session.close()
