"""Admin trigger endpoints — LOCAL/DEV ONLY, NO AUTH.

WARNING: these endpoints WRITE data and spend API-Football quota + DeepSeek
tokens. They are intentionally unauthenticated for local/dev convenience. Do
NOT mount this router behind a public ingress without adding authentication.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


class TriggerResult(BaseModel):
    status: str  # "ok" | "error"
    action: str  # "collect" | "run-brief"
    date: date
    exit_code: int
    detail: str


def _resolve_date(date_str: str | None) -> date:
    """Use the given YYYY-MM-DD, else today's date in the brief timezone."""
    if date_str:
        return date.fromisoformat(date_str)
    return datetime.now(tz=ZoneInfo(settings.BRIEF_TIMEZONE)).date()


@router.post("/collect", response_model=TriggerResult)
def trigger_collect(for_date: str | None = Query(default=None, alias="date")) -> TriggerResult:
    """Fetch + persist matches/standings for a date (no LLM). Blocks until done."""
    from app.data.collect import run as collect_run

    target = _resolve_date(for_date)
    code = collect_run(target)
    return TriggerResult(
        status="ok" if code == 0 else "error",
        action="collect",
        date=target,
        exit_code=code,
        detail="data collected" if code == 0 else "collection failed (see server logs)",
    )


@router.post("/run-brief", response_model=TriggerResult)
def trigger_run_brief(for_date: str | None = Query(default=None, alias="date")) -> TriggerResult:
    """Run the full pipeline (collect -> generate + publish brief). Blocks until done."""
    from app.pipeline.run import run_pipeline

    target = _resolve_date(for_date)
    code = run_pipeline(target)
    return TriggerResult(
        status="ok" if code == 0 else "error",
        action="run-brief",
        date=target,
        exit_code=code,
        detail="brief published" if code == 0 else "pipeline failed (last-good preserved)",
    )
