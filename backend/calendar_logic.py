# backend/calendar_logic.py
"""
Calendar logic for event filtering and conflict detection.

This file provides helper functions for working with calendar events,
such as checking for scheduling conflicts, filtering events by date,
and retrieving upcoming events within a given time range.
"""

from datetime import datetime, timedelta
from typing import List, Optional


# Parse a datetime string into a naive datetime object.
def parse_time(time_str: str) -> Optional[datetime]:
    if time_str is None:
        return None
    try:
        dt = datetime.fromisoformat(time_str)
        # Strip timezone info to ensure consistent naive datetime comparisons.
        return dt.replace(tzinfo=None)
    except ValueError:
        return None


# Check whether two events overlap in time.
def check_event_conflict(event1: dict, event2: dict) -> bool:
    start1 = parse_time(event1.get("start_time"))
    end1 = parse_time(event1.get("end_time"))
    start2 = parse_time(event2.get("start_time"))
    end2 = parse_time(event2.get("end_time"))

    if start1 is None or start2 is None:
        return False

    if end1 is None:
        end1 = start1
    if end2 is None:
        end2 = start2

    return start1 < end2 and start2 < end1


# Return all events that fall on a specific date, including multi-day events.
def get_events_for_date(events: List[dict], date: str) -> List[dict]:
    try:
        target = datetime.fromisoformat(date).date()
    except ValueError:
        return []

    result = []
    for event in events:
        start = parse_time(event.get("start_time"))
        end = parse_time(event.get("end_time")) or start
        if start and start.date() <= target <= end.date():
            result.append(event)
    return result


# Check whether an event has already passed.
def is_event_past(event: dict) -> bool:
    start = parse_time(event.get("start_time"))
    if start is None:
        return False
    return start < datetime.now()


# Return events starting within the next given number of days.
def get_upcoming_events(events: List[dict], days: int = 7) -> List[dict]:
    now = datetime.now()
    cutoff = now + timedelta(days=days)

    result = []
    for event in events:
        start = parse_time(event.get("start_time"))
        if start and now <= start <= cutoff:
            result.append(event)
    return result