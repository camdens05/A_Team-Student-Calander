# backend/event_factory.py
"""
Factory logic for event creation.

This file will create different types of calendar events, such as
appointments, recurring events, and all-day events, based on user input.
It keeps event creation organized and avoids repeated conditional logic
throughout the application.
"""

from models import Event, AppointmentEvent, RecurringEvent, AllDayEvent