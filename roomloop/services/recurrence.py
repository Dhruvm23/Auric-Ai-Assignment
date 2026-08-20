"""DST-aware weekly recurrence generator.

Given a first-occurrence wall-clock time and a timezone, yields naive local
datetimes for every weekly repetition up to repeat_until.  Each occurrence is
computed from the IANA timezone so that wall-clock time is preserved across
DST transitions — this is what R3 requires and what was broken in the old
prototype (Denver bookings drifted by one hour around spring-forward).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def weekly_occurrences(
    start_local: str,
    end_local: str,
    repeat_until: str,
    timezone: str,
) -> list[tuple[str, str]]:
    """Return list of (start_naive_iso, end_naive_iso) for every weekly slot.

    All returned strings are naive ISO (no offset) — ready to store per C1.
    """
    tz = ZoneInfo(timezone)

    anchor_start = datetime.fromisoformat(start_local)
    anchor_end = datetime.fromisoformat(end_local)
    until = datetime.fromisoformat(repeat_until)

    duration = anchor_end - anchor_start

    hour, minute = anchor_start.hour, anchor_start.minute
    target_weekday = anchor_start.weekday()

    occurrences: list[tuple[str, str]] = []
    current_date = anchor_start.date()

    while True:
        candidate = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            hour,
            minute,
        )

        if candidate > until:
            break

        aware = candidate.replace(tzinfo=tz)
        naive_start = aware.replace(tzinfo=None)
        naive_end = (naive_start + duration)

        fmt = "%Y-%m-%dT%H:%M:%S"
        occurrences.append((naive_start.strftime(fmt), naive_end.strftime(fmt)))

        current_date += timedelta(weeks=1)

    return occurrences
