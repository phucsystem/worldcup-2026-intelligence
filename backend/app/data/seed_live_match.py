"""Flip one stored match into a live state for demoing the in-progress card
without a paid API plan / a real in-play game.

  python -m app.data.seed_live_match                 # auto-pick a fixture
  python -m app.data.seed_live_match --fixture-id N  # target a specific one
  python -m app.data.seed_live_match --clear         # revert seeded row to FT

Picks the most recent fixture by kickoff when none is given. Sets status=2H,
a sample score, and elapsed=67 with a fresh updated_at so /api/fixtures/live
returns it and the frontend minute interpolates from "now".
"""
import argparse
import logging
import sys
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.data.repository import make_session_factory, matches_table

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _pick_fixture_id(session) -> int | None:
    row = session.execute(
        select(matches_table.c.fixture_id)
        .where(matches_table.c.kickoff_utc.isnot(None))
        .order_by(matches_table.c.kickoff_utc.desc())
    ).first()
    return row[0] if row else None


def seed(fixture_id: int | None, clear: bool) -> int:
    session_factory = make_session_factory()
    now = datetime.now(tz=timezone.utc)
    with session_factory() as session:
        fid = fixture_id or _pick_fixture_id(session)
        if fid is None:
            log.error("No fixtures in DB to seed")
            return 1
        if clear:
            values = {"status": "FT", "elapsed": None, "updated_at": now}
        else:
            values = {
                "status": "2H",
                "home_score": 2,
                "away_score": 1,
                "elapsed": 67,
                "updated_at": now,
            }
        result = session.execute(
            update(matches_table).where(matches_table.c.fixture_id == fid).values(**values)
        )
        session.commit()
        if result.rowcount:
            log.info("%s fixture %s (%s)", "Cleared" if clear else "Seeded live", fid, values["status"])
        else:
            log.warning("Fixture %s not found", fid)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed/clear a live match for demo")
    parser.add_argument("--fixture-id", type=int, default=None)
    parser.add_argument("--clear", action="store_true", help="revert the row to FT")
    args = parser.parse_args()
    sys.exit(seed(args.fixture_id, args.clear))


if __name__ == "__main__":
    main()
