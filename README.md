# RoomLoop — Meeting Room Booking Service

A Python REST API for booking meeting rooms, supporting single bookings, DST-aware weekly recurring bookings, conflict detection, and series cancellation.

Built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

## Quick Start

```bash
# Clone and install
git clone <repo-url> && cd roomloop
pip install -r requirements.txt

# Run the server
uvicorn roomloop.main:app --reload

# Server starts at http://127.0.0.1:8000
# Interactive API docs at http://127.0.0.1:8000/docs
```

## Run Tests

```bash
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database — no setup required.

## API Reference

### Rooms

**GET /rooms** — List all rooms (C2-compatible response shape).

```bash
curl http://127.0.0.1:8000/rooms
```

```json
[
  {"id": 3, "name": "Aurora", "capacity": 8},
  {"id": 4, "name": "Basalt", "capacity": 4},
  {"id": 9, "name": "Cinder", "capacity": 12},
  {"id": 17, "name": "Dune", "capacity": 6}
]
```

### Single Booking

**POST /bookings** — Create a booking. Returns `409` on conflict.

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 3,
    "user": "alice",
    "start_time": "2026-09-01T09:00:00",
    "end_time": "2026-09-01T10:00:00"
  }'
```

### Recurring Booking

**POST /bookings/recurring** — Create a weekly series. Conflicting instances are skipped (R2); the rest are created atomically (R1).

```bash
curl -X POST http://127.0.0.1:8000/bookings/recurring \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 3,
    "user": "alice",
    "start_time": "2026-09-07T09:00:00",
    "end_time": "2026-09-07T10:00:00",
    "repeat_until": "2026-12-28T23:59:00",
    "timezone": "Europe/Berlin"
  }'
```

The `timezone` field accepts IANA timezone names (`Europe/Berlin`, `America/Denver`). This ensures recurring bookings repeat at the correct wall-clock time across DST transitions.

### Cancel a Booking

**DELETE /bookings/{id}** — Cancel a single booking (soft delete).

```bash
curl -X DELETE http://127.0.0.1:8000/bookings/1
```

### Cancel a Series

**DELETE /series/{id}** — Cancel all **future** instances of a recurring series. Past instances remain active.

```bash
curl -X DELETE http://127.0.0.1:8000/series/1
```

### List / Filter Bookings

**GET /bookings** — Supports optional query parameters: `room_id`, `date_from`, `date_to`, `status`.

```bash
# All active bookings in room 3
curl "http://127.0.0.1:8000/bookings?room_id=3&status=active"

# Bookings in a date range
curl "http://127.0.0.1:8000/bookings?date_from=2026-09-01T00:00:00&date_to=2026-09-30T23:59:00"
```

**GET /bookings/{id}** — Get a single booking by ID.

## Architecture

```
roomloop/
  main.py              FastAPI app with lifespan
  database.py          SQLAlchemy engine + session
  models.py            Room, Booking, Series ORM models
  schemas.py           Pydantic request/response schemas
  seed.py              Seed rooms on startup
  routers/
    rooms.py           GET /rooms
    bookings.py        All booking + series endpoints
  services/
    booking_service.py Conflict check, create, cancel logic
    recurrence.py      DST-aware weekly occurrence generator
tests/
  test_rooms.py        C2 response shape compliance
  test_single_booking.py
  test_conflicts.py    R4: overlap, back-to-back, cross-room
  test_recurring_booking.py  R1 + R2: atomicity + skip conflicts
  test_cancellation.py       Single + series cancellation
  test_dst.py          DST edge cases (Denver, Berlin)
```

## Key Design Points

- **Timestamps**: Stored and returned as naive local ISO strings (`2026-09-01T09:00:00`) — no offset, no `Z`. This preserves compatibility with the nightly reporting job (C1).
- **DST handling**: The `timezone` on a recurring series drives occurrence generation via Python's `zoneinfo`. Wall-clock time is preserved across DST transitions — this fixes the Denver hour-off issue from last winter.
- **Conflict detection**: Strict inequality (`start < other_end AND end > other_start`) so back-to-back bookings are allowed (R4).
- **Soft delete**: Cancelled bookings keep their data with `status: "cancelled"` for auditability.
# Auric-Ai-Assignment
