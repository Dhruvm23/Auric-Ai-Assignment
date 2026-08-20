"""R4: conflict detection — overlapping bookings in the same room are rejected,
back-to-back bookings and different rooms are allowed."""


def _book(client, room_id, start, end, user="tester"):
    return client.post("/bookings", json={
        "room_id": room_id, "user": user,
        "start_time": start, "end_time": end,
    })


def test_exact_overlap_rejected(client):
    assert _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T10:00:00").status_code == 201
    assert _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T10:00:00").status_code == 409


def test_partial_overlap_rejected(client):
    assert _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T10:00:00").status_code == 201
    assert _book(client, 3, "2026-09-01T09:30:00", "2026-09-01T10:30:00").status_code == 409


def test_enclosing_overlap_rejected(client):
    assert _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T11:00:00").status_code == 201
    assert _book(client, 3, "2026-09-01T09:30:00", "2026-09-01T10:30:00").status_code == 409


def test_back_to_back_allowed(client):
    """R4: one ends 10:00, next starts 10:00 — NOT a conflict."""
    assert _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T10:00:00").status_code == 201
    assert _book(client, 3, "2026-09-01T10:00:00", "2026-09-01T11:00:00").status_code == 201


def test_different_rooms_no_conflict(client):
    assert _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T10:00:00").status_code == 201
    assert _book(client, 4, "2026-09-01T09:00:00", "2026-09-01T10:00:00").status_code == 201


def test_cancelled_booking_no_conflict(client):
    """A cancelled booking should not block a new booking in the same slot."""
    resp = _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T10:00:00")
    assert resp.status_code == 201
    booking_id = resp.json()["id"]

    client.delete(f"/bookings/{booking_id}")

    assert _book(client, 3, "2026-09-01T09:00:00", "2026-09-01T10:00:00").status_code == 201
