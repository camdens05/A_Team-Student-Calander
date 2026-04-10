# backend/database.py
"""
Database setup and connection logic.

This file will handle connecting to the database, creating tables if
needed, and providing helper functions for saving and retrieving user
and event data. It keeps storage logic separated from the rest of the app.
"""

import sqlite3
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "student_calendar.db"


# Open a SQLite connection with row access by column name.
def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# Create all database tables and indexes if they do not already exist.
def init_db() -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                preferences TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                recurrence_rule TEXT,
                is_all_day INTEGER NOT NULL DEFAULT 0,
                reminder_minutes INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS canvas_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                canvas_course_id TEXT,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT,
                url TEXT,
                synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_user_id
            ON events(user_id);
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_start_time
            ON events(start_time);
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_user_id
            ON tasks(user_id);
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canvas_items_user_id
            ON canvas_items(user_id);
            """
        )

        conn.commit()


# Convert one SQLite row into a standard Python dictionary.
def dict_from_row(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


# Convert a list of SQLite rows into a list of dictionaries.
def dicts_from_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


# Insert a new user record and return its database id.
def create_user(
    username: str,
    email: str,
    password_hash: Optional[str] = None,
    preferences: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, preferences)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, preferences),
        )
        conn.commit()
        return int(cursor.lastrowid)


# Fetch one user by id.
def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict_from_row(row)


# Fetch one user by email address.
def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        return dict_from_row(row)


# Insert a new calendar event and return its database id.
def create_event(
    user_id: int,
    title: str,
    event_type: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    recurrence_rule: Optional[str] = None,
    is_all_day: bool = False,
    reminder_minutes: Optional[int] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO events (
                user_id, title, description, event_type, start_time, end_time,
                location, recurrence_rule, is_all_day, reminder_minutes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                description,
                event_type,
                start_time,
                end_time,
                location,
                recurrence_rule,
                int(is_all_day),
                reminder_minutes,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


# Fetch one event by id.
def get_event_by_id(event_id: int) -> Optional[dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE id = ?",
            (event_id,),
        ).fetchone()
        return dict_from_row(row)


# Fetch all events that belong to one user.
def get_events_by_user(user_id: int) -> list[dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM events
            WHERE user_id = ?
            ORDER BY start_time ASC
            """,
            (user_id,),
        ).fetchall()
        return dicts_from_rows(rows)


# Update allowed event fields and return whether a row was changed.
def update_event(event_id: int, **fields: Any) -> bool:
    allowed_fields = {
        "title",
        "description",
        "event_type",
        "start_time",
        "end_time",
        "location",
        "recurrence_rule",
        "is_all_day",
        "reminder_minutes",
    }

    updates = []
    values = []

    for key, value in fields.items():
        if key in allowed_fields:
            updates.append(f"{key} = ?")
            if key == "is_all_day":
                values.append(int(bool(value)))
            else:
                values.append(value)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(event_id)

    with get_db_connection() as conn:
        cursor = conn.execute(
            f"""
            UPDATE events
            SET {', '.join(updates)}
            WHERE id = ?
            """,
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount > 0


# Delete one event by id and return whether a row was removed.
def delete_event(event_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM events WHERE id = ?",
            (event_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


# Insert a new task and return its database id.
def create_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    status: str = "pending",
) -> int:
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (user_id, title, description, due_date, priority, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, due_date, priority, status),
        )
        conn.commit()
        return int(cursor.lastrowid)


# Fetch all tasks that belong to one user.
def get_tasks_by_user(user_id: int) -> list[dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE user_id = ?
            ORDER BY due_date ASC, created_at ASC
            """,
            (user_id,),
        ).fetchall()
        return dicts_from_rows(rows)


# Close a database connection if one was provided.
def close_connection(conn: Optional[sqlite3.Connection]) -> None:
    if conn is not None:
        conn.close()