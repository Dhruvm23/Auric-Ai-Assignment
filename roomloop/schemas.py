from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator


NAIVE_FMT = "%Y-%m-%dT%H:%M:%S"


def _parse_naive(v: str | datetime) -> str:
    """Accept a naive ISO string or datetime and return a clean naive ISO string."""
    if isinstance(v, datetime):
        return v.strftime(NAIVE_FMT)
    dt = datetime.fromisoformat(v)
    return dt.strftime(NAIVE_FMT)


# ── Rooms ──────────────────────────────────────────────────────────────


class RoomOut(BaseModel):
    id: int
    name: str
    capacity: int

    model_config = {"from_attributes": True}


# ── Bookings ───────────────────────────────────────────────────────────


class BookingCreate(BaseModel):
    room_id: int
    user: str
    start_time: str
    end_time: str

    @field_validator("start_time", "end_time")
    @classmethod
    def normalise_timestamp(cls, v: str) -> str:
        return _parse_naive(v)

    @model_validator(mode="after")
    def end_after_start(self) -> BookingCreate:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class BookingOut(BaseModel):
    id: int
    room_id: int
    user: str
    start_time: str
    end_time: str
    series_id: int | None = None
    status: str

    model_config = {"from_attributes": True}


# ── Recurring bookings ─────────────────────────────────────────────────


class RecurringBookingCreate(BaseModel):
    room_id: int
    user: str
    start_time: str
    end_time: str
    repeat_until: str
    timezone: str

    @field_validator("start_time", "end_time", "repeat_until")
    @classmethod
    def normalise_timestamp(cls, v: str) -> str:
        return _parse_naive(v)

    @model_validator(mode="after")
    def end_after_start(self) -> RecurringBookingCreate:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class RecurringBookingOut(BaseModel):
    series_id: int
    created: list[BookingOut]
    skipped: list[dict]
    total_occurrences: int
