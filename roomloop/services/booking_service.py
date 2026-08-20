"""Core booking logic: conflict checking, single/recurring creation, cancellation."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from roomloop.models import Booking, Series, Room
from roomloop.services.recurrence import weekly_occurrences


def _has_conflict(db: Session, room_id: int, start: str, end: str, exclude_id: int | None = None) -> bool:
    """True if an active booking overlaps [start, end) in the given room.

    Uses strict inequality so back-to-back bookings (one ends 10:00, next
    starts 10:00) are NOT conflicts — per R4.
    """
    q = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status == "active",
        Booking.start_time < end,
        Booking.end_time > start,
    )
    if exclude_id is not None:
        q = q.filter(Booking.id != exclude_id)
    return q.first() is not None


def _validate_room(db: Session, room_id: int) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise ValueError(f"Room {room_id} does not exist")
    return room


def create_single_booking(db: Session, room_id: int, user: str, start_time: str, end_time: str) -> Booking:
    _validate_room(db, room_id)

    if _has_conflict(db, room_id, start_time, end_time):
        raise ValueError(f"Time slot conflicts with an existing booking in room {room_id}")

    booking = Booking(
        room_id=room_id,
        user=user,
        start_time=start_time,
        end_time=end_time,
        status="active",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def create_recurring_booking(
    db: Session,
    room_id: int,
    user: str,
    start_time: str,
    end_time: str,
    repeat_until: str,
    timezone: str,
) -> dict:
    """Create a recurring weekly booking series.

    R1: atomic — either all non-conflicting instances are saved, or none.
    R2: conflicting instances are skipped, not failed.
    """
    _validate_room(db, room_id)

    occurrences = weekly_occurrences(start_time, end_time, repeat_until, timezone)

    if not occurrences:
        raise ValueError("No occurrences generated for the given parameters")

    first = datetime.fromisoformat(occurrences[0][0])

    series = Series(
        room_id=room_id,
        user=user,
        start_time_local=start_time,
        end_time_local=end_time,
        day_of_week=first.weekday(),
        repeat_until=repeat_until,
        timezone=timezone,
    )
    db.add(series)
    db.flush()

    created: list[Booking] = []
    skipped: list[dict] = []

    for occ_start, occ_end in occurrences:
        if _has_conflict(db, room_id, occ_start, occ_end):
            skipped.append({"start_time": occ_start, "end_time": occ_end, "reason": "conflict"})
            continue

        booking = Booking(
            room_id=room_id,
            user=user,
            start_time=occ_start,
            end_time=occ_end,
            series_id=series.id,
            status="active",
        )
        db.add(booking)
        created.append(booking)

    if not created:
        db.rollback()
        raise ValueError("All occurrences conflict with existing bookings; nothing created")

    db.commit()
    for b in created:
        db.refresh(b)

    return {
        "series_id": series.id,
        "created": created,
        "skipped": skipped,
        "total_occurrences": len(occurrences),
    }


def cancel_booking(db: Session, booking_id: int) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking is None:
        raise LookupError(f"Booking {booking_id} not found")
    if booking.status == "cancelled":
        raise ValueError(f"Booking {booking_id} is already cancelled")

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking


def cancel_series(db: Session, series_id: int) -> dict:
    """Cancel all future instances of a series. Past instances stay active."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if series is None:
        raise LookupError(f"Series {series_id} not found")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    future_bookings = (
        db.query(Booking)
        .filter(
            Booking.series_id == series_id,
            Booking.status == "active",
            Booking.start_time >= now,
        )
        .all()
    )

    cancelled_ids = []
    for b in future_bookings:
        b.status = "cancelled"
        cancelled_ids.append(b.id)

    db.commit()

    return {
        "series_id": series_id,
        "cancelled_count": len(cancelled_ids),
        "cancelled_booking_ids": cancelled_ids,
    }
