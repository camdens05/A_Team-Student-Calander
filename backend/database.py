# backend/database.py
"""
Database setup and connection logic.

This file will handle connecting to the database, creating tables if
needed, and providing helper functions for saving and retrieving user
and event data. It keeps storage logic separated from the rest of the app.
"""

import sqlite3