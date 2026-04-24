import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import unittest
from datetime import datetime, timedelta
from calendar_logic import (
    parse_time,
    check_event_conflict,
    get_events_for_date,
    is_event_past,
    get_upcoming_events,
)


# ── parse_time ────────────────────────────────────────────────────────────────

class TestParseTime(unittest.TestCase):

    def test_space_separated_datetime(self):
        result = parse_time("2026-05-01 10:00:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 5)
        self.assertEqual(result.hour, 10)

    def test_iso_format_with_T(self):
        result = parse_time("2026-05-01T10:00:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 10)

    def test_none_input_returns_none(self):
        self.assertIsNone(parse_time(None))

    def test_invalid_string_returns_none(self):
        self.assertIsNone(parse_time("not-a-date"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_time(""))

    def test_timezone_aware_string_stripped_to_naive(self):
        result = parse_time("2026-05-01T10:00:00+05:00")
        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo)

    def test_returns_naive_datetime(self):
        result = parse_time("2026-05-01 10:00:00")
        self.assertIsNone(result.tzinfo)


# ── check_event_conflict ──────────────────────────────────────────────────────

class TestCheckEventConflict(unittest.TestCase):

    def _ev(self, start, end=None):
        return {"start_time": start, "end_time": end}

    def test_overlapping_events_conflict(self):
        e1 = self._ev("2026-05-01 10:00:00", "2026-05-01 12:00:00")
        e2 = self._ev("2026-05-01 11:00:00", "2026-05-01 13:00:00")
        self.assertTrue(check_event_conflict(e1, e2))

    def test_non_overlapping_events_no_conflict(self):
        e1 = self._ev("2026-05-01 09:00:00", "2026-05-01 10:00:00")
        e2 = self._ev("2026-05-01 11:00:00", "2026-05-01 12:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_adjacent_events_no_conflict(self):
        # e1 ends exactly when e2 starts — boundary is exclusive
        e1 = self._ev("2026-05-01 09:00:00", "2026-05-01 10:00:00")
        e2 = self._ev("2026-05-01 10:00:00", "2026-05-01 11:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_e1_contains_e2(self):
        e1 = self._ev("2026-05-01 08:00:00", "2026-05-01 18:00:00")
        e2 = self._ev("2026-05-01 10:00:00", "2026-05-01 11:00:00")
        self.assertTrue(check_event_conflict(e1, e2))

    def test_missing_start_time_returns_false(self):
        e1 = {"start_time": None, "end_time": "2026-05-01 10:00:00"}
        e2 = self._ev("2026-05-01 09:00:00", "2026-05-01 11:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_both_missing_start_times_returns_false(self):
        e1 = {"start_time": None, "end_time": None}
        e2 = {"start_time": None, "end_time": None}
        self.assertFalse(check_event_conflict(e1, e2))

    def test_missing_end_time_treated_as_point_event(self):
        # Point event at the same time: start1 < end2 → T < T is False → no conflict
        e1 = self._ev("2026-05-01 10:00:00")
        e2 = self._ev("2026-05-01 10:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_e2_entirely_before_e1(self):
        e1 = self._ev("2026-05-01 14:00:00", "2026-05-01 16:00:00")
        e2 = self._ev("2026-05-01 10:00:00", "2026-05-01 12:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_conflict_is_symmetric(self):
        e1 = self._ev("2026-05-01 10:00:00", "2026-05-01 12:00:00")
        e2 = self._ev("2026-05-01 11:00:00", "2026-05-01 13:00:00")
        self.assertEqual(check_event_conflict(e1, e2), check_event_conflict(e2, e1))


# ── get_events_for_date ───────────────────────────────────────────────────────

class TestGetEventsForDate(unittest.TestCase):

    def _ev(self, start, end=None, title="Event"):
        return {"title": title, "start_time": start, "end_time": end}

    def test_event_on_exact_date_returned(self):
        events = [self._ev("2026-05-01 10:00:00", "2026-05-01 11:00:00", "Match")]
        result = get_events_for_date(events, "2026-05-01")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Match")

    def test_event_on_different_date_excluded(self):
        events = [self._ev("2026-05-02 10:00:00", "2026-05-02 11:00:00")]
        result = get_events_for_date(events, "2026-05-01")
        self.assertEqual(result, [])

    def test_multi_day_event_spans_target_date(self):
        events = [self._ev("2026-05-01 00:00:00", "2026-05-03 23:59:00", "Multi")]
        result = get_events_for_date(events, "2026-05-02")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Multi")

    def test_event_with_no_start_time_excluded(self):
        events = [{"title": "No start", "start_time": None, "end_time": None}]
        result = get_events_for_date(events, "2026-05-01")
        self.assertEqual(result, [])

    def test_invalid_date_string_returns_empty(self):
        events = [self._ev("2026-05-01 10:00:00")]
        result = get_events_for_date(events, "not-a-date")
        self.assertEqual(result, [])

    def test_empty_events_list(self):
        self.assertEqual(get_events_for_date([], "2026-05-01"), [])

    def test_filters_multiple_events_correctly(self):
        events = [
            self._ev("2026-05-01 09:00:00", title="A"),
            self._ev("2026-05-02 09:00:00", title="B"),
            self._ev("2026-05-01 14:00:00", title="C"),
        ]
        result = get_events_for_date(events, "2026-05-01")
        titles = {e["title"] for e in result}
        self.assertEqual(titles, {"A", "C"})
        self.assertNotIn("B", titles)

    def test_event_starting_on_date_with_no_end_included(self):
        events = [self._ev("2026-05-01 08:00:00", title="NoEnd")]
        result = get_events_for_date(events, "2026-05-01")
        self.assertEqual(len(result), 1)


# ── is_event_past ─────────────────────────────────────────────────────────────

class TestIsEventPast(unittest.TestCase):

    def test_past_event_returns_true(self):
        ev = {"start_time": "2020-01-01 10:00:00"}
        self.assertTrue(is_event_past(ev))

    def test_future_event_returns_false(self):
        ev = {"start_time": "2099-01-01 10:00:00"}
        self.assertFalse(is_event_past(ev))

    def test_none_start_returns_false(self):
        self.assertFalse(is_event_past({"start_time": None}))

    def test_missing_start_key_returns_false(self):
        self.assertFalse(is_event_past({}))

    def test_invalid_start_string_returns_false(self):
        self.assertFalse(is_event_past({"start_time": "bad-date"}))


# ── get_upcoming_events ───────────────────────────────────────────────────────

class TestGetUpcomingEvents(unittest.TestCase):

    def _ev(self, offset_days, title="Event"):
        dt = datetime.now() + timedelta(days=offset_days)
        return {"title": title, "start_time": dt.strftime("%Y-%m-%d %H:%M:%S")}

    def test_events_within_window_included(self):
        events = [self._ev(1, "Tomorrow"), self._ev(3, "In3Days")]
        result = get_upcoming_events(events, days=7)
        titles = {e["title"] for e in result}
        self.assertIn("Tomorrow", titles)
        self.assertIn("In3Days", titles)

    def test_events_outside_window_excluded(self):
        events = [self._ev(10, "TooFar")]
        result = get_upcoming_events(events, days=7)
        self.assertEqual(result, [])

    def test_past_events_excluded(self):
        events = [self._ev(-1, "Yesterday")]
        result = get_upcoming_events(events, days=7)
        self.assertEqual(result, [])

    def test_custom_days_window_respected(self):
        events = [self._ev(3, "In3"), self._ev(8, "In8")]
        result = get_upcoming_events(events, days=5)
        titles = {e["title"] for e in result}
        self.assertIn("In3", titles)
        self.assertNotIn("In8", titles)

    def test_empty_events_list(self):
        self.assertEqual(get_upcoming_events([], days=7), [])

    def test_event_with_none_start_excluded(self):
        events = [{"title": "No start", "start_time": None}]
        self.assertEqual(get_upcoming_events(events, days=7), [])

    def test_default_window_is_seven_days(self):
        events = [self._ev(6, "In6"), self._ev(8, "In8")]
        result = get_upcoming_events(events)  # default days=7
        titles = {e["title"] for e in result}
        self.assertIn("In6", titles)
        self.assertNotIn("In8", titles)


if __name__ == "__main__":
    unittest.main()
