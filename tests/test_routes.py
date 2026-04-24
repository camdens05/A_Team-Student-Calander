import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import database


class TestRoutes(unittest.TestCase):
    """
    Integration tests for the Flask API routes.
    Each test runs against a fresh temporary SQLite database.
    """

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.patcher = patch.object(database, "DB_PATH", Path(self.tmp.name))
        self.patcher.start()
        database.init_db()

        import app as app_module
        flask_app = app_module.create_app()
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

        # A real user is required to satisfy the foreign key constraint on events
        self.user_id = database.create_user("testuser", "test@example.com")

    def tearDown(self):
        self.patcher.stop()
        import gc
        gc.collect()  # release any SQLite connections held by CPython's refcount GC
        try:
            os.unlink(self.tmp.name)
        except PermissionError:
            pass  # Windows may keep the file locked briefly; the OS will clean it up

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _post_event(self, **overrides):
        payload = {
            "user_id": self.user_id,
            "title": "Test Event",
            "event_type": "event",
            "start_time": "2026-05-01 10:00:00",
            **overrides,
        }
        return self.client.post(
            "/api/events",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def _get_first_event_id(self):
        events = self.client.get(f"/api/events?user_id={self.user_id}").get_json()
        return events[0]["id"]

    # ── GET /api/health ───────────────────────────────────────────────────────

    def test_health_check_returns_ok(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "ok")

    # ── GET /api/events ───────────────────────────────────────────────────────

    def test_get_events_missing_user_id_returns_400(self):
        resp = self.client.get("/api/events")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("user_id is required", resp.get_json()["error"])

    def test_get_events_empty_list_for_new_user(self):
        resp = self.client.get(f"/api/events?user_id={self.user_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), [])

    def test_get_events_returns_created_events(self):
        self._post_event(title="MyEvent")
        resp = self.client.get(f"/api/events?user_id={self.user_id}")
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "MyEvent")

    def test_get_events_returns_only_the_requesting_users_events(self):
        other_uid = database.create_user("other", "other@example.com")
        database.create_event(
            user_id=other_uid, title="OtherEvent",
            event_type="event", start_time="2026-05-01 10:00:00"
        )
        self._post_event(title="MyEvent")
        resp = self.client.get(f"/api/events?user_id={self.user_id}")
        titles = [e["title"] for e in resp.get_json()]
        self.assertIn("MyEvent", titles)
        self.assertNotIn("OtherEvent", titles)

    # ── GET /api/events/<id> ──────────────────────────────────────────────────

    def test_get_event_by_id_not_found_returns_404(self):
        resp = self.client.get("/api/events/9999")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("error", resp.get_json())

    def test_get_event_by_id_found_returns_200(self):
        self._post_event(title="Findme")
        event_id = self._get_first_event_id()
        resp = self.client.get(f"/api/events/{event_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["title"], "Findme")

    # ── POST /api/events ──────────────────────────────────────────────────────

    def test_create_event_success_returns_201(self):
        resp = self._post_event()
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "Test Event")

    def test_create_event_returns_created_record(self):
        resp = self._post_event(
            title="Exam",
            event_type="appointment",
            start_time="2026-06-01 09:00:00",
            end_time="2026-06-01 10:00:00",
            location="Hall A",
        )
        data = resp.get_json()
        self.assertEqual(data["title"], "Exam")
        self.assertEqual(data["event_type"], "appointment")
        self.assertEqual(data["location"], "Hall A")

    def test_create_event_no_body_returns_400(self):
        resp = self.client.post("/api/events", content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_create_event_missing_required_fields_returns_400(self):
        resp = self.client.post(
            "/api/events",
            data=json.dumps({"user_id": self.user_id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Missing required fields", resp.get_json()["error"])

    def test_create_event_invalid_type_returns_400(self):
        resp = self._post_event(event_type="invalid_type")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid event type", resp.get_json()["error"])

    def test_create_allday_event_sets_is_all_day(self):
        resp = self._post_event(event_type="allday")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["is_all_day"], 1)

    def test_create_recurring_event_type_stored(self):
        resp = self._post_event(event_type="recurring", recurrence_rule="WEEKLY")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["event_type"], "recurring")

    # ── PUT /api/events/<id> ──────────────────────────────────────────────────

    def test_update_event_success_returns_200(self):
        self._post_event(title="Original")
        event_id = self._get_first_event_id()
        resp = self.client.put(
            f"/api/events/{event_id}",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["title"], "Updated")

    def test_update_event_multiple_fields(self):
        self._post_event()
        event_id = self._get_first_event_id()
        resp = self.client.put(
            f"/api/events/{event_id}",
            data=json.dumps({"title": "New Title", "location": "Room 5", "reminder_minutes": 10}),
            content_type="application/json",
        )
        data = resp.get_json()
        self.assertEqual(data["title"], "New Title")
        self.assertEqual(data["location"], "Room 5")
        self.assertEqual(data["reminder_minutes"], 10)

    def test_update_event_not_found_returns_404(self):
        resp = self.client.put(
            "/api/events/9999",
            data=json.dumps({"title": "Nope"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_update_event_no_valid_fields_returns_400(self):
        self._post_event()
        event_id = self._get_first_event_id()
        resp = self.client.put(
            f"/api/events/{event_id}",
            data=json.dumps({"not_a_real_field": "value"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("No valid fields", resp.get_json()["error"])

    def test_update_event_no_body_returns_400(self):
        self._post_event()
        event_id = self._get_first_event_id()
        resp = self.client.put(f"/api/events/{event_id}", content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    # ── DELETE /api/events/<id> ───────────────────────────────────────────────

    def test_delete_event_success_returns_200(self):
        self._post_event()
        event_id = self._get_first_event_id()
        resp = self.client.delete(f"/api/events/{event_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("deleted", resp.get_json()["message"])

    def test_delete_event_not_found_returns_404(self):
        resp = self.client.delete("/api/events/9999")
        self.assertEqual(resp.status_code, 404)

    def test_delete_event_removes_record(self):
        self._post_event()
        event_id = self._get_first_event_id()
        self.client.delete(f"/api/events/{event_id}")
        resp = self.client.get(f"/api/events/{event_id}")
        self.assertEqual(resp.status_code, 404)

    def test_delete_event_reduces_event_count(self):
        self._post_event(title="A")
        self._post_event(title="B")
        event_id = self._get_first_event_id()
        self.client.delete(f"/api/events/{event_id}")
        events = self.client.get(f"/api/events?user_id={self.user_id}").get_json()
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
