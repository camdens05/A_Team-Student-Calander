# backend/routes.py
"""
API route definitions.

This file will contain the backend endpoints for handling requests from
the frontend, such as creating events, viewing events, updating events,
and deleting events. It connects user actions in the interface to backend logic.
"""

from models import Event
from event_factory import create_event_object
from database import get_db_connection

from flask import jsonify, request

from database import (
    create_event,
    delete_event,
    get_event_by_id,
    get_events_by_user,
    update_event,
)


# Register all API routes with the Flask app.
def register_routes(app):
    # Simple health check route to confirm the backend is running.
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"}), 200

    # Return all events for a specific user.
    @app.route("/api/events", methods=["GET"])
    def fetch_events():
        user_id = request.args.get("user_id", type=int)

        if user_id is None:
            return jsonify({"error": "user_id is required"}), 400

        events = get_events_by_user(user_id)
        return jsonify(events), 200

    # Return one event by its database id.
    @app.route("/api/events/<int:event_id>", methods=["GET"])
    def fetch_event(event_id):
        event = get_event_by_id(event_id)

        if event is None:
            return jsonify({"error": "Event not found"}), 404

        return jsonify(event), 200

    # Create a new calendar event from request data.
    @app.route("/api/events", methods=["POST"])
    def add_event():
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        required_fields = ["user_id", "title", "event_type", "start_time"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        try:
            # Use event_factory to validate and build the correct event object
            event_obj = create_event_object(data["event_type"], data)

            event_id = create_event(
                user_id=event_obj.user_id,
                title=event_obj.title,
                event_type=event_obj.event_type,
                start_time=event_obj.start_time,
                end_time=event_obj.end_time,
                description=event_obj.description,
                location=event_obj.location,
                recurrence_rule=event_obj.recurrence_rule,
                is_all_day=event_obj.is_all_day,
                reminder_minutes=event_obj.reminder_minutes,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

        new_event = get_event_by_id(event_id)
        return jsonify(new_event), 201

    # Update an existing event using the provided JSON fields.
    @app.route("/api/events/<int:event_id>", methods=["PUT"])
    def edit_event(event_id):
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        event = get_event_by_id(event_id)
        if event is None:
            return jsonify({"error": "Event not found"}), 404

        updated = update_event(event_id, **data)
        if not updated:
            return jsonify({"error": "No valid fields were provided for update"}), 400

        updated_event = get_event_by_id(event_id)
        return jsonify(updated_event), 200

    # Delete an event by id.
    @app.route("/api/events/<int:event_id>", methods=["DELETE"])
    def remove_event(event_id):
        event = get_event_by_id(event_id)
        if event is None:
            return jsonify({"error": "Event not found"}), 404

        deleted = delete_event(event_id)
        if not deleted:
            return jsonify({"error": "Failed to delete event"}), 500

        return jsonify({"message": "Event deleted successfully"}), 200