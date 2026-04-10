# backend/routes.py
"""
API route definitions.

This file will contain the backend endpoints for handling requests from
the frontend, such as creating events, viewing events, updating events,
and deleting events. It connects user actions in the interface to backend logic.
"""

from flask import request, jsonify
from models import Event
from event_factory import create_event
from database import get_db_connection