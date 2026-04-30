# backend/models.py
"""
Data models for the application.

This file will define the main data structures used in the system, such
as users and calendar events. It gives the backend a consistent way to
represent and organize application data.
"""

from dataclasses import dataclass
from typing import Optional


# Base data model for a general calendar event.
@dataclass
class Event:
    user_id: int
    title: str
    event_type: str
    start_time: str
    end_time: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    recurrence_rule: Optional[str] = None
    is_all_day: bool = False
    reminder_minutes: Optional[int] = None
    priority: Optional[str] = None
    course: Optional[str] = None
    url: Optional[str] = None

    # Return the event data as a dictionary.
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "title": self.title,
            "event_type": self.event_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "location": self.location,
            "recurrence_rule": self.recurrence_rule,
            "is_all_day": self.is_all_day,
            "reminder_minutes": self.reminder_minutes,
            "priority": self.priority,
            "course": self.course,
            "url": self.url,
        }


# Data model for an appointment event.
@dataclass
class AppointmentEvent(Event):
    # Set the event type for appointment events after initialization.
    def __post_init__(self):
        self.event_type = "appointment"


# Data model for a recurring calendar event.
@dataclass
class RecurringEvent(Event):
    # Set the event type for recurring events after initialization.
    def __post_init__(self):
        self.event_type = "recurring"


# Data model for an all-day calendar event.
@dataclass
class AllDayEvent(Event):
    # Set the event type and all-day flag after initialization.
    def __post_init__(self):
        self.event_type = "allday"
        self.is_all_day = True