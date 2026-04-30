# A-Team Student Calendar

A web-based calendar and planner built for students. Create and manage events by type — class, assignment, exam, study session, appointment, recurring, and all-day — with conflict detection, priority ranking, and per-event course and URL tracking.

## Setup

**Requirements:** Python 3.8+

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

**Start the backend** (terminal 1):
```bash
cd backend
python app.py
```

**Start the frontend** (terminal 2):
```bash
cd frontend
python -m http.server 8000
```

Open `http://localhost:8000`. The frontend connects to the backend at `http://localhost:5000`.

## Running Tests

```bash
pytest tests/ --cov=backend --cov-report=term-missing -v
```

Run a single test:
```bash
pytest tests/test_calendar_logic.py::TestConflictDetection::test_overlapping_events -v
```

## Features

- Monthly calendar view that opens to the current date
- Seven event types: Class, Assignment, Exam, Study Session, Appointment, Recurring, All-Day
- Per-event priority (low / medium / high), course label, and related URL
- Recurrence presets (daily, weekly, Mon/Wed/Fri, Tue/Thu, monthly) plus custom RRULE input
- Conflict detection when scheduling overlapping events
- Upcoming events sidebar sorted by start time
- Multi-user support via user ID selection (persisted in `localStorage`)

## Project Structure

```
backend/          Flask REST API (port 5000)
frontend/         Vanilla JS + HTML/CSS (static files)
tests/            unittest test suite with SQLite temp-file isolation
requirements.txt  Python dependencies
pyproject.toml    Pytest and coverage configuration
```

## API

All endpoints are prefixed with `/api`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/events?user_id=<id>` | List events for a user |
| GET | `/events/<id>` | Get a single event |
| POST | `/events` | Create an event |
| PUT | `/events/<id>` | Update an event |
| DELETE | `/events/<id>` | Delete an event |
