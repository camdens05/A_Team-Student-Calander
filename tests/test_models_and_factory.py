import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import unittest
from models import Event, AppointmentEvent, RecurringEvent, AllDayEvent
from event_factory import create_event_object


# ── Helpers ───────────────────────────────────────────────────────────────────

BASE_DATA = {
    "user_id": 1,
    "title": "Test Event",
    "start_time": "2026-05-01 10:00:00",
    "event_type": "event",
}


def make_event(**kwargs):
    defaults = {
        "user_id": 1,
        "title": "Test Event",
        "event_type": "event",
        "start_time": "2026-05-01 10:00:00",
        "end_time": None,
        "description": None,
        "location": None,
        "recurrence_rule": None,
        "is_all_day": False,
        "reminder_minutes": None,
    }
    defaults.update(kwargs)
    return Event(**defaults)


# ── Event model ───────────────────────────────────────────────────────────────

class TestEventModel(unittest.TestCase):

    def test_basic_creation(self):
        ev = make_event()
        self.assertEqual(ev.user_id, 1)
        self.assertEqual(ev.title, "Test Event")
        self.assertEqual(ev.event_type, "event")
        self.assertEqual(ev.start_time, "2026-05-01 10:00:00")

    def test_optional_fields_default_to_none_or_false(self):
        ev = make_event()
        self.assertIsNone(ev.end_time)
        self.assertIsNone(ev.description)
        self.assertIsNone(ev.location)
        self.assertIsNone(ev.recurrence_rule)
        self.assertFalse(ev.is_all_day)
        self.assertIsNone(ev.reminder_minutes)

    def test_to_dict_contains_all_keys(self):
        ev = make_event()
        expected = {
            "user_id", "title", "event_type", "start_time", "end_time",
            "description", "location", "recurrence_rule", "is_all_day",
            "reminder_minutes",
        }
        self.assertEqual(set(ev.to_dict().keys()), expected)

    def test_to_dict_values_match_fields(self):
        ev = make_event(description="Study", location="Library", reminder_minutes=15)
        d = ev.to_dict()
        self.assertEqual(d["description"], "Study")
        self.assertEqual(d["location"], "Library")
        self.assertEqual(d["reminder_minutes"], 15)
        self.assertFalse(d["is_all_day"])

    def test_to_dict_none_fields_included(self):
        ev = make_event()
        d = ev.to_dict()
        self.assertIsNone(d["end_time"])
        self.assertIsNone(d["description"])


# ── Subclass models ───────────────────────────────────────────────────────────

class TestSubclassModels(unittest.TestCase):

    def _base(self, **kwargs):
        return {**BASE_DATA, **kwargs}

    def test_appointment_event_sets_type(self):
        ev = AppointmentEvent(**self._base())
        self.assertEqual(ev.event_type, "appointment")

    def test_recurring_event_sets_type(self):
        ev = RecurringEvent(**self._base())
        self.assertEqual(ev.event_type, "recurring")

    def test_allday_event_sets_type_and_flag(self):
        ev = AllDayEvent(**self._base())
        self.assertEqual(ev.event_type, "allday")
        self.assertTrue(ev.is_all_day)

    def test_appointment_to_dict_reflects_type(self):
        ev = AppointmentEvent(**self._base())
        self.assertEqual(ev.to_dict()["event_type"], "appointment")

    def test_allday_to_dict_is_all_day_true(self):
        ev = AllDayEvent(**self._base())
        self.assertTrue(ev.to_dict()["is_all_day"])


# ── Event factory ─────────────────────────────────────────────────────────────

class TestCreateEventObject(unittest.TestCase):

    def test_creates_base_event(self):
        obj = create_event_object("event", BASE_DATA)
        self.assertIsInstance(obj, Event)
        self.assertEqual(obj.event_type, "event")

    def test_creates_appointment(self):
        obj = create_event_object("appointment", BASE_DATA)
        self.assertIsInstance(obj, AppointmentEvent)
        self.assertEqual(obj.event_type, "appointment")

    def test_creates_recurring(self):
        obj = create_event_object("recurring", BASE_DATA)
        self.assertIsInstance(obj, RecurringEvent)
        self.assertEqual(obj.event_type, "recurring")

    def test_creates_allday(self):
        obj = create_event_object("allday", BASE_DATA)
        self.assertIsInstance(obj, AllDayEvent)
        self.assertTrue(obj.is_all_day)

    def test_creates_allday_hyphen_variant(self):
        obj = create_event_object("all-day", BASE_DATA)
        self.assertIsInstance(obj, AllDayEvent)

    def test_creates_allday_underscore_variant(self):
        obj = create_event_object("all_day", BASE_DATA)
        self.assertIsInstance(obj, AllDayEvent)

    def test_type_is_case_insensitive(self):
        obj = create_event_object("APPOINTMENT", BASE_DATA)
        self.assertIsInstance(obj, AppointmentEvent)

    def test_type_strips_whitespace(self):
        obj = create_event_object("  event  ", BASE_DATA)
        self.assertIsInstance(obj, Event)

    def test_invalid_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            create_event_object("unknown_type", BASE_DATA)

    def test_optional_fields_passed_through(self):
        data = {
            **BASE_DATA,
            "end_time": "2026-05-01 11:00:00",
            "location": "Room 101",
            "reminder_minutes": 10,
            "description": "A note",
        }
        obj = create_event_object("event", data)
        self.assertEqual(obj.end_time, "2026-05-01 11:00:00")
        self.assertEqual(obj.location, "Room 101")
        self.assertEqual(obj.reminder_minutes, 10)
        self.assertEqual(obj.description, "A note")

    def test_missing_optional_fields_default_to_none(self):
        obj = create_event_object("event", BASE_DATA)
        self.assertIsNone(obj.end_time)
        self.assertIsNone(obj.description)
        self.assertIsNone(obj.location)
        self.assertIsNone(obj.recurrence_rule)
        self.assertIsNone(obj.reminder_minutes)

    def test_recurring_passes_recurrence_rule(self):
        data = {**BASE_DATA, "recurrence_rule": "WEEKLY"}
        obj = create_event_object("recurring", data)
        self.assertEqual(obj.recurrence_rule, "WEEKLY")


if __name__ == "__main__":
    unittest.main()
