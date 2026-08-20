"""Cancellation: single bookings and series (future-only)."""

from unittest.mock import patch
from datetime import datetime


def test_cancel_single_booking(client):
    resp = client.post("/bookings", json={
        "room_id": 3, "user": "alice",
        "start_time": "2026-09-01T09:00:00", "end_time": "2026-09-01T10:00:00",
    })
    booking_id = resp.json()["id"]

    resp = client.delete(f"/bookings/{booking_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_already_cancelled(client):
    resp = client.post("/bookings", json={
        "room_id": 3, "user": "alice",
        "start_time": "2026-09-01T09:00:00", "end_time": "2026-09-01T10:00:00",
    })
    booking_id = resp.json()["id"]
    client.delete(f"/bookings/{booking_id}")

    resp = client.delete(f"/bookings/{booking_id}")
    assert resp.status_code == 409


def test_cancel_nonexistent(client):
    resp = client.delete("/bookings/99999")
    assert resp.status_code == 404


def test_cancel_series_future_only(client):
    """Office manager requirement: cancel series kills future instances, keeps past."""
    resp = client.post("/bookings/recurring", json={
        "room_id": 3, "user": "alice",
        "start_time": "2026-08-03T09:00:00",
        "end_time": "2026-08-03T10:00:00",
        "repeat_until": "2026-09-28T23:59:00",
        "timezone": "Europe/Berlin",
    })
    data = resp.json()
    series_id = data["series_id"]
    all_bookings = data["created"]

    fake_now = "2026-08-25T00:00:00"
    with patch("roomloop.services.booking_service.datetime") as mock_dt:
        mock_dt.now.return_value = datetime.fromisoformat(fake_now)
        mock_dt.fromisoformat = datetime.fromisoformat

        resp = client.delete(f"/series/{series_id}")
        assert resp.status_code == 200
        result = resp.json()
        assert result["cancelled_count"] > 0

    past_ids = [b["id"] for b in all_bookings if b["start_time"] < fake_now]
    future_ids = [b["id"] for b in all_bookings if b["start_time"] >= fake_now]

    for bid in past_ids:
        r = client.get(f"/bookings/{bid}")
        assert r.json()["status"] == "active"

    for bid in future_ids:
        r = client.get(f"/bookings/{bid}")
        assert r.json()["status"] == "cancelled"


def test_cancel_nonexistent_series(client):
    resp = client.delete("/series/99999")
    assert resp.status_code == 404
