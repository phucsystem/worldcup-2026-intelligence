"""Unit tests for the live poller's pure window-gating logic — no DB, no network."""

from datetime import datetime, timedelta, timezone

from app.pipeline.live_poller import should_poll_now


def _dt(h, m=0):
    return datetime(2026, 6, 19, h, m, tzinfo=timezone.utc)


NOW = _dt(20)  # 20:00 UTC


class TestShouldPollNow:
    def test_kicked_off_recently_is_in_window(self):
        # kicked off 30 min ago → in play
        assert should_poll_now([_dt(19, 30)], NOW)

    def test_future_kickoff_is_not_in_window(self):
        # kicks off in 2 hours
        assert not should_poll_now([_dt(22)], NOW)

    def test_past_window_is_not_in_window(self):
        # kicked off 4 hours ago, past the 3h window
        assert not should_poll_now([_dt(16)], NOW)

    def test_empty_is_not_in_window(self):
        assert not should_poll_now([], NOW)

    def test_none_kickoffs_are_ignored(self):
        assert not should_poll_now([None, None], NOW)

    def test_any_in_window_returns_true(self):
        # one future, one in-window → True
        assert should_poll_now([_dt(22), _dt(19, 45)], NOW)

    def test_custom_window(self):
        # kicked off 90 min ago is outside a 1h window
        assert not should_poll_now([_dt(18, 30)], NOW, window=timedelta(hours=1))
