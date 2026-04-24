import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import database


class TestDatabase(unittest.TestCase):
    """Tests use a temporary file-based SQLite DB so no real data is touched."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.patcher = patch.object(database, "DB_PATH", Path(self.tmp.name))
        self.patcher.start()
        database.init_db()

    def tearDown(self):
        self.patcher.stop()
        import gc
        gc.collect()  # release any SQLite connections held by CPython's refcount GC
        try:
            os.unlink(self.tmp.name)
        except PermissionError:
            pass  # Windows may keep the file locked briefly; the OS will clean it up

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _create_user(self, username="testuser", email="test@example.com"):
        return database.create_user(username, email)

    def _create_event(self, user_id, **kwargs):
        defaults = {
            "title": "Test Event",
            "event_type": "event",
            "start_time": "2026-05-01 10:00:00",
        }
        defaults.update(kwargs)
        return database.create_event(user_id=user_id, **defaults)

    # ── Utility functions ─────────────────────────────────────────────────────

    def test_dict_from_row_none_returns_none(self):
        self.assertIsNone(database.dict_from_row(None))

    def test_dicts_from_rows_empty_list(self):
        self.assertEqual(database.dicts_from_rows([]), [])

    def test_get_db_connection_returns_connection(self):
        conn = database.get_db_connection()
        self.assertIsNotNone(conn)
        database.close_connection(conn)

    def test_close_connection_with_none_does_not_raise(self):
        database.close_connection(None)

    def test_close_connection_closes_open_conn(self):
        conn = database.get_db_connection()
        database.close_connection(conn)  # should not raise

    # ── Users — create ────────────────────────────────────────────────────────

    def test_create_user_returns_int_id(self):
        uid = self._create_user()
        self.assertIsInstance(uid, int)
        self.assertGreater(uid, 0)

    def test_create_multiple_users_distinct_ids(self):
        uid1 = self._create_user("alice", "alice@example.com")
        uid2 = self._create_user("bob", "bob@example.com")
        self.assertNotEqual(uid1, uid2)

    # ── Users — get by id ─────────────────────────────────────────────────────

    def test_get_user_by_id_returns_correct_user(self):
        uid = self._create_user("alice", "alice@example.com")
        user = database.get_user_by_id(uid)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "alice")
        self.assertEqual(user["email"], "alice@example.com")

    def test_get_user_by_id_not_found_returns_none(self):
        self.assertIsNone(database.get_user_by_id(9999))

    # ── Users — get by email ──────────────────────────────────────────────────

    def test_get_user_by_email_returns_correct_user(self):
        uid = self._create_user("bob", "bob@example.com")
        user = database.get_user_by_email("bob@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], uid)

    def test_get_user_by_email_not_found_returns_none(self):
        self.assertIsNone(database.get_user_by_email("nobody@example.com"))

    # ── Events — create ───────────────────────────────────────────────────────

    def test_create_event_returns_int_id(self):
        uid = self._create_user()
        event_id = self._create_event(uid)
        self.assertIsInstance(event_id, int)
        self.assertGreater(event_id, 0)

    def test_create_event_with_all_fields(self):
        uid = self._create_user()
        event_id = database.create_event(
            user_id=uid,
            title="Full Event",
            event_type="appointment",
            start_time="2026-05-01 10:00:00",
            end_time="2026-05-01 11:00:00",
            description="A note",
            location="Room 202",
            recurrence_rule="WEEKLY",
            is_all_day=False,
            reminder_minutes=15,
        )
        ev = database.get_event_by_id(event_id)
        self.assertEqual(ev["description"], "A note")
        self.assertEqual(ev["location"], "Room 202")
        self.assertEqual(ev["recurrence_rule"], "WEEKLY")
        self.assertEqual(ev["reminder_minutes"], 15)
        self.assertEqual(ev["end_time"], "2026-05-01 11:00:00")

    # ── Events — get by id ────────────────────────────────────────────────────

    def test_get_event_by_id_returns_correct_event(self):
        uid = self._create_user()
        event_id = self._create_event(uid, title="Math Exam")
        ev = database.get_event_by_id(event_id)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["title"], "Math Exam")
        self.assertEqual(ev["user_id"], uid)

    def test_get_event_by_id_not_found_returns_none(self):
        self.assertIsNone(database.get_event_by_id(9999))

    # ── Events — get by user ──────────────────────────────────────────────────

    def test_get_events_by_user_returns_all_user_events(self):
        uid = self._create_user()
        self._create_event(uid, title="A")
        self._create_event(uid, title="B")
        events = database.get_events_by_user(uid)
        self.assertEqual(len(events), 2)

    def test_get_events_by_user_empty_for_unknown_user(self):
        self.assertEqual(database.get_events_by_user(9999), [])

    def test_get_events_by_user_ordered_by_start_time(self):
        uid = self._create_user()
        self._create_event(uid, title="Later",   start_time="2026-06-01 10:00:00")
        self._create_event(uid, title="Earlier", start_time="2026-05-01 10:00:00")
        events = database.get_events_by_user(uid)
        self.assertEqual(events[0]["title"], "Earlier")
        self.assertEqual(events[1]["title"], "Later")

    def test_get_events_by_user_does_not_return_other_users_events(self):
        uid1 = self._create_user("u1", "u1@example.com")
        uid2 = self._create_user("u2", "u2@example.com")
        self._create_event(uid1, title="User1Event")
        events = database.get_events_by_user(uid2)
        self.assertEqual(events, [])

    # ── Events — update ───────────────────────────────────────────────────────

    def test_update_event_title_returns_true(self):
        uid = self._create_user()
        eid = self._create_event(uid, title="Old")
        result = database.update_event(eid, title="New")
        self.assertTrue(result)

    def test_update_event_title_persisted(self):
        uid = self._create_user()
        eid = self._create_event(uid, title="Old")
        database.update_event(eid, title="New")
        self.assertEqual(database.get_event_by_id(eid)["title"], "New")

    def test_update_event_multiple_fields(self):
        uid = self._create_user()
        eid = self._create_event(uid)
        database.update_event(eid, title="Updated", location="Room 101", reminder_minutes=30)
        ev = database.get_event_by_id(eid)
        self.assertEqual(ev["title"], "Updated")
        self.assertEqual(ev["location"], "Room 101")
        self.assertEqual(ev["reminder_minutes"], 30)

    def test_update_event_invalid_field_returns_false(self):
        uid = self._create_user()
        eid = self._create_event(uid)
        result = database.update_event(eid, nonexistent_field="value")
        self.assertFalse(result)

    def test_update_event_is_all_day_coerced_to_int(self):
        uid = self._create_user()
        eid = self._create_event(uid)
        database.update_event(eid, is_all_day=True)
        self.assertEqual(database.get_event_by_id(eid)["is_all_day"], 1)

    def test_update_event_false_is_all_day_coerced_to_zero(self):
        uid = self._create_user()
        eid = self._create_event(uid)
        database.update_event(eid, is_all_day=False)
        self.assertEqual(database.get_event_by_id(eid)["is_all_day"], 0)

    # ── Events — delete ───────────────────────────────────────────────────────

    def test_delete_event_returns_true(self):
        uid = self._create_user()
        eid = self._create_event(uid)
        self.assertTrue(database.delete_event(eid))

    def test_delete_event_removes_record(self):
        uid = self._create_user()
        eid = self._create_event(uid)
        database.delete_event(eid)
        self.assertIsNone(database.get_event_by_id(eid))

    def test_delete_nonexistent_event_returns_false(self):
        self.assertFalse(database.delete_event(9999))

    # ── Tasks — create ────────────────────────────────────────────────────────

    def test_create_task_returns_int_id(self):
        uid = self._create_user()
        task_id = database.create_task(user_id=uid, title="Finish homework")
        self.assertIsInstance(task_id, int)
        self.assertGreater(task_id, 0)

    def test_create_task_with_optional_fields(self):
        uid = self._create_user()
        task_id = database.create_task(
            user_id=uid,
            title="Essay",
            description="Write 5 pages",
            due_date="2026-05-10",
            priority="high",
            status="in_progress",
        )
        self.assertGreater(task_id, 0)

    # ── Tasks — get by user ───────────────────────────────────────────────────

    def test_get_tasks_by_user_returns_all_tasks(self):
        uid = self._create_user()
        database.create_task(uid, "Task 1")
        database.create_task(uid, "Task 2")
        tasks = database.get_tasks_by_user(uid)
        self.assertEqual(len(tasks), 2)

    def test_get_tasks_by_user_empty_for_unknown_user(self):
        self.assertEqual(database.get_tasks_by_user(9999), [])

    def test_get_tasks_by_user_does_not_return_other_users_tasks(self):
        uid1 = self._create_user("u1", "u1@example.com")
        uid2 = self._create_user("u2", "u2@example.com")
        database.create_task(uid1, "User1 Task")
        self.assertEqual(database.get_tasks_by_user(uid2), [])


if __name__ == "__main__":
    unittest.main()
