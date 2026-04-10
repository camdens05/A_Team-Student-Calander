# backend/event_factory.py
"""
Factory logic for event creation.

This file will create different types of calendar events, such as
appointments, recurring events, and all-day events, based on user input.
It keeps event creation organized and avoids repeated conditional logic
throughout the application.
"""

from models import AllDayEvent, AppointmentEvent, Event, RecurringEvent


# Create the correct event object based on the provided event type.
def create_event_object(event_type: str, data: dict) -> Event:
    normalized_type = event_type.strip().lower()

    common_args = {
        "user_id": data["user_id"],
        "title": data["title"],
        "start_time": data["start_time"],
        "end_time": data.get("end_time"),
        "description": data.get("description"),
        "location": data.get("location"),
        "recurrence_rule": data.get("recurrence_rule"),
        "reminder_minutes": data.get("reminder_minutes"),
        "event_type": normalized_type,
    }

    if normalized_type == "event":
        return Event(**common_args)

    if normalized_type == "appointment":
        return AppointmentEvent(**common_args)

    if normalized_type == "recurring":
        return RecurringEvent(**common_args)

    if normalized_type in {"allday", "all-day", "all_day"}:
        return AllDayEvent(**common_args)

    raise ValueError(f"Invalid event type: {event_type}")