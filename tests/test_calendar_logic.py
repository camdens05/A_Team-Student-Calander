# tests/test_calendar_logic.py
"""
Unit and integration tests for backend/calendar_logic.py.

AI-generated with Claude. Prompt used:
  "Given this calendar_logic.py with functions parse_time, check_event_conflict,
   get_events_for_date, is_event_past, and get_upcoming_events, generate unit tests
   (at least one per function) and one integration test."
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from calendar_logic import (
    parse_time,
    check_event_conflict,
    get_events_for_date,
    is_event_past,
    get_upcoming_events,
)


# ─── parse_time ───────────────────────────────────────────────────────────────

class TestParseTime(unittest.TestCase):

    def test_valid_iso_with_T_separator(self):
        # Standard ISO format used by HTML datetime-local inputs
        result = parse_time("2025-04-20T10:00:00")
        self.assertEqual(result, datetime(2025, 4, 20, 10, 0, 0))

    def test_valid_space_separator(self):
        # Space-separated format used by SQLite storage
        result = parse_time("2025-04-20 10:00:00")
        self.assertEqual(result, datetime(2025, 4, 20, 10, 0, 0))

    def test_returns_none_for_none_input(self):
        self.assertIsNone(parse_time(None))

    def test_returns_none_for_invalid_string(self):
        self.assertIsNone(parse_time("not-a-date"))

    def test_strips_timezone_info(self):
        # Result should be naive (no tzinfo)
        result = parse_time("2025-04-20T10:00:00+05:00")
        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo)


# ─── check_event_conflict ─────────────────────────────────────────────────────

class TestCheckEventConflict(unittest.TestCase):

    def _make_event(self, start, end=None):
        e = {"start_time": start}
        if end:
            e["end_time"] = end
        return e

    def test_overlapping_events_conflict(self):
        e1 = self._make_event("2025-04-20 10:00:00", "2025-04-20 12:00:00")
        e2 = self._make_event("2025-04-20 11:00:00", "2025-04-20 13:00:00")
        self.assertTrue(check_event_conflict(e1, e2))

    def test_non_overlapping_events_no_conflict(self):
        e1 = self._make_event("2025-04-20 08:00:00", "2025-04-20 09:00:00")
        e2 = self._make_event("2025-04-20 10:00:00", "2025-04-20 11:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_adjacent_events_no_conflict(self):
        # End of one equals start of the other — should NOT conflict
        e1 = self._make_event("2025-04-20 08:00:00", "2025-04-20 10:00:00")
        e2 = self._make_event("2025-04-20 10:00:00", "2025-04-20 12:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_missing_start_time_returns_false(self):
        e1 = {"title": "No time"}
        e2 = self._make_event("2025-04-20 10:00:00", "2025-04-20 11:00:00")
        self.assertFalse(check_event_conflict(e1, e2))

    def test_missing_end_time_treated_as_point(self):
        # Events with no end_time are treated as instant (point in time)
        e1 = self._make_event("2025-04-20 10:00:00")
        e2 = self._make_event("2025-04-20 10:00:00")
        # Two identical points: start1 < end2 → 10:00 < 10:00 is False → no conflict
        self.assertFalse(check_event_conflict(e1, e2))


# ─── get_events_for_date ──────────────────────────────────────────────────────

class TestGetEventsForDate(unittest.TestCase):

    def setUp(self):
        self.events = [
            {"title": "Morning", "start_time": "2025-04-20 08:00:00", "end_time": "2025-04-20 09:00:00"},
            {"title": "Afternoon", "start_time": "2025-04-20 14:00:00", "end_time": "2025-04-20 15:00:00"},
            {"title": "Next Day", "start_time": "2025-04-21 10:00:00", "end_time": "2025-04-21 11:00:00"},
            {"title": "Multi-day", "start_time": "2025-04-19 00:00:00", "end_time": "2025-04-21 00:00:00"},
        ]

    def test_returns_events_on_target_date(self):
        result = get_events_for_date(self.events, "2025-04-20")
        titles = [e["title"] for e in result]
        self.assertIn("Morning", titles)
        self.assertIn("Afternoon", titles)

    def test_excludes_events_on_other_dates(self):
        result = get_events_for_date(self.events, "2025-04-20")
        titles = [e["title"] for e in result]
        self.assertNotIn("Next Day", titles)

    def test_includes_multi_day_events(self):
        result = get_events_for_date(self.events, "2025-04-20")
        titles = [e["title"] for e in result]
        self.assertIn("Multi-day", titles)

    def test_returns_empty_for_date_with_no_events(self):
        result = get_events_for_date(self.events, "2025-05-01")
        self.assertEqual(result, [])

    def test_returns_empty_for_invalid_date_string(self):
        result = get_events_for_date(self.events, "not-a-date")
        self.assertEqual(result, [])


# ─── is_event_past ────────────────────────────────────────────────────────────

class TestIsEventPast(unittest.TestCase):

    def test_past_event_returns_true(self):
        past = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        event = {"start_time": past}
        self.assertTrue(is_event_past(event))

    def test_future_event_returns_false(self):
        future = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        event = {"start_time": future}
        self.assertFalse(is_event_past(event))

    def test_missing_start_time_returns_false(self):
        self.assertFalse(is_event_past({}))


# ─── get_upcoming_events ──────────────────────────────────────────────────────

class TestGetUpcomingEvents(unittest.TestCase):

    def setUp(self):
        now = datetime.now()
        self.events = [
            {"title": "Tomorrow", "start_time": (now + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")},
            {"title": "In 5 days", "start_time": (now + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")},
            {"title": "In 10 days", "start_time": (now + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")},
            {"title": "Yesterday", "start_time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")},
        ]

    def test_returns_events_within_default_7_days(self):
        result = get_upcoming_events(self.events)
        titles = [e["title"] for e in result]
        self.assertIn("Tomorrow", titles)
        self.assertIn("In 5 days", titles)

    def test_excludes_events_beyond_window(self):
        result = get_upcoming_events(self.events)
        titles = [e["title"] for e in result]
        self.assertNotIn("In 10 days", titles)

    def test_excludes_past_events(self):
        result = get_upcoming_events(self.events)
        titles = [e["title"] for e in result]
        self.assertNotIn("Yesterday", titles)

    def test_custom_days_window(self):
        result = get_upcoming_events(self.events, days=14)
        titles = [e["title"] for e in result]
        self.assertIn("In 10 days", titles)

    def test_empty_event_list(self):
        self.assertEqual(get_upcoming_events([]), [])


# ─── Integration test ─────────────────────────────────────────────────────────

class TestCalendarLogicIntegration(unittest.TestCase):
    """
    Integration test: simulates a realistic workflow where events are fetched,
    filtered by date, checked for conflicts, and checked for upcoming status.
    """

    def test_full_workflow(self):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        events = [
            {
                "title": "Team standup",
                "start_time": now.strftime("%Y-%m-%d") + " 09:00:00",
                "end_time":   now.strftime("%Y-%m-%d") + " 09:30:00",
            },
            {
                "title": "Design review",
                "start_time": now.strftime("%Y-%m-%d") + " 09:15:00",
                "end_time":   now.strftime("%Y-%m-%d") + " 10:00:00",
            },
            {
                "title": "Lunch",
                "start_time": now.strftime("%Y-%m-%d") + " 12:00:00",
                "end_time":   now.strftime("%Y-%m-%d") + " 13:00:00",
            },
            {
                "title": "Next week meeting",
                "start_time": (now + timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
                "end_time":   (now + timedelta(days=8, hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            },
        ]

        # Step 1: filter to today's events
        todays = get_events_for_date(events, today_str)
        self.assertEqual(len(todays), 3)

        # Step 2: check conflict between standup and design review (they overlap)
        standup = next(e for e in todays if e["title"] == "Team standup")
        design  = next(e for e in todays if e["title"] == "Design review")
        self.assertTrue(check_event_conflict(standup, design))

        # Step 3: standup and lunch do not conflict
        lunch = next(e for e in todays if e["title"] == "Lunch")
        self.assertFalse(check_event_conflict(standup, lunch))

        # Step 4: upcoming events within 7 days should not include next week
        upcoming = get_upcoming_events(events, days=7)
        upcoming_titles = [e["title"] for e in upcoming]
        self.assertNotIn("Next week meeting", upcoming_titles)


if __name__ == "__main__":
    unittest.main()