# tests/test_events.py
"""
Event functionality tests.

This file will contain tests for the core event-related functionality of
the application, such as creating events, validating event types, and
ensuring the factory logic produces the correct event objects. It helps
verify that the main scheduling features work correctly.
"""

import unittest
from backend.event_factory import create_event
from backend.models import Event