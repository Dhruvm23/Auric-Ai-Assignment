"""Single booking creation and basic validation."""


def test_create_booking(client):
    resp = client.post("/bookings", json={
        "room_id": 3,
        "user": "alice",
        "start_time": "2026-09-01T09:00:00",
        "end_time": "2026-09-01T10:00:00",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["room_id"] == 3
    assert data["user"] == "alice"
    assert data["status"] == "active"
    assert data["series_id"] is None


def test_create_booking_invalid_room(client):
    resp = client.post("/bookings", json={
        "room_id": 999,
        "user": "alice",
        "start_time": "2026-09-01T09:00:00",
        "end_time": "2026-09-01T10:00:00",
    })
    assert resp.status_code == 409


def test_create_booking_end_before_start(client):
    resp = client.post("/bookings", json={
        "room_id": 3,
        "user": "alice",
        "start_time": "2026-09-01T10:00:00",
        "end_time": "2026-09-01T09:00:00",
    })
    assert resp.status_code == 422


def test_c1_naive_timestamp_format(client):
    """C1: timestamps must be naive ISO strings without offset or Z."""
    resp = client.post("/bookings", json={
        "room_id": 3,
        "user": "alice",
        "start_time": "2026-09-01T09:00:00",
        "end_time": "2026-09-01T10:00:00",
    })
    data = resp.json()
    assert "+" not in data["start_time"]
    assert "Z" not in data["start_time"]
    assert data["start_time"] == "2026-09-01T09:00:00"


def test_get_booking(client):
    create = client.post("/bookings", json={
        "room_id": 3,
        "user": "bob",
        "start_time": "2026-09-02T14:00:00",
        "end_time": "2026-09-02T15:00:00",
    })
    booking_id = create.json()["id"]

    resp = client.get(f"/bookings/{booking_id}")
    assert resp.status_code == 200
    assert resp.json()["user"] == "bob"


def test_get_booking_not_found(client):
    resp = client.get("/bookings/99999")
    assert resp.status_code == 404
