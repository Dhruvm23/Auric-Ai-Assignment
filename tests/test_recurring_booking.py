"""Recurring booking creation: R1 (atomicity) and R2 (skip conflicts)."""


def test_create_recurring_basic(client):
    """4 Mondays in September 2026."""
    resp = client.post("/bookings/recurring", json={
        "room_id": 3,
        "user": "alice",
        "start_time": "2026-09-07T09:00:00",
        "end_time": "2026-09-07T10:00:00",
        "repeat_until": "2026-09-28T23:59:00",
        "timezone": "Europe/Berlin",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["series_id"] is not None
    assert data["total_occurrences"] == 4
    assert len(data["created"]) == 4
    assert len(data["skipped"]) == 0

    for b in data["created"]:
        assert b["series_id"] == data["series_id"]
        assert b["status"] == "active"


def test_recurring_skips_conflicts(client):
    """R2: pre-book 2 of 4 slots, recurring should create the other 2."""
    client.post("/bookings", json={
        "room_id": 3, "user": "blocker",
        "start_time": "2026-09-07T09:00:00", "end_time": "2026-09-07T10:00:00",
    })
    client.post("/bookings", json={
        "room_id": 3, "user": "blocker",
        "start_time": "2026-09-21T09:00:00", "end_time": "2026-09-21T10:00:00",
    })

    resp = client.post("/bookings/recurring", json={
        "room_id": 3,
        "user": "alice",
        "start_time": "2026-09-07T09:00:00",
        "end_time": "2026-09-07T10:00:00",
        "repeat_until": "2026-09-28T23:59:00",
        "timezone": "Europe/Berlin",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_occurrences"] == 4
    assert len(data["created"]) == 2
    assert len(data["skipped"]) == 2


def test_recurring_all_conflicts_fails(client):
    """R1: if ALL occurrences conflict, nothing is saved."""
    for day in ["07", "14", "21", "28"]:
        client.post("/bookings", json={
            "room_id": 3, "user": "blocker",
            "start_time": f"2026-09-{day}T09:00:00",
            "end_time": f"2026-09-{day}T10:00:00",
        })

    resp = client.post("/bookings/recurring", json={
        "room_id": 3,
        "user": "alice",
        "start_time": "2026-09-07T09:00:00",
        "end_time": "2026-09-07T10:00:00",
        "repeat_until": "2026-09-28T23:59:00",
        "timezone": "Europe/Berlin",
    })
    assert resp.status_code == 409


def test_recurring_bookings_linked_by_series(client):
    resp = client.post("/bookings/recurring", json={
        "room_id": 4,
        "user": "charlie",
        "start_time": "2026-10-06T14:00:00",
        "end_time": "2026-10-06T15:00:00",
        "repeat_until": "2026-10-27T23:59:00",
        "timezone": "America/Denver",
    })
    data = resp.json()
    series_id = data["series_id"]
    assert all(b["series_id"] == series_id for b in data["created"])
