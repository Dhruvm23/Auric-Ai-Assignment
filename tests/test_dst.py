"""DST edge cases — the core of why Denver bookings were an hour off.

R3: recurring bookings repeat at the same wall-clock time.
The old prototype likely stored UTC or applied a fixed offset, so when Denver
switched from MST (UTC-7) to MDT (UTC-6) in spring, bookings shifted by an hour.

Our approach: generate each occurrence in the target timezone using zoneinfo,
then strip the offset before storing.  Wall-clock time is preserved.
"""

from roomloop.services.recurrence import weekly_occurrences


def test_denver_spring_forward():
    """Denver DST: 2026-03-08 clocks spring forward (MST -> MDT).

    A weekly Monday 9:00 AM booking should stay at 09:00 local time
    both before and after the transition.
    """
    occurrences = weekly_occurrences(
        start_local="2026-03-02T09:00:00",
        end_local="2026-03-02T10:00:00",
        repeat_until="2026-03-23T23:59:00",
        timezone="America/Denver",
    )

    assert len(occurrences) == 4
    for start, end in occurrences:
        assert "T09:00:00" in start
        assert "T10:00:00" in end


def test_denver_fall_back():
    """Denver DST: 2026-11-01 clocks fall back (MDT -> MST).

    Wall-clock time should remain 09:00 on both sides.
    """
    occurrences = weekly_occurrences(
        start_local="2026-10-26T09:00:00",
        end_local="2026-10-26T10:00:00",
        repeat_until="2026-11-16T23:59:00",
        timezone="America/Denver",
    )

    assert len(occurrences) == 4
    for start, end in occurrences:
        assert "T09:00:00" in start
        assert "T10:00:00" in end


def test_berlin_spring_forward():
    """Berlin DST: 2026-03-29 clocks spring forward (CET -> CEST).

    Weekly Thursday 10:00 should stay at 10:00 local.
    """
    occurrences = weekly_occurrences(
        start_local="2026-03-19T10:00:00",
        end_local="2026-03-19T11:00:00",
        repeat_until="2026-04-09T23:59:00",
        timezone="Europe/Berlin",
    )

    assert len(occurrences) == 4
    for start, end in occurrences:
        assert "T10:00:00" in start
        assert "T11:00:00" in end


def test_berlin_fall_back():
    """Berlin DST: 2026-10-25 clocks fall back (CEST -> CET)."""
    occurrences = weekly_occurrences(
        start_local="2026-10-12T14:00:00",
        end_local="2026-10-12T15:00:00",
        repeat_until="2026-11-02T23:59:00",
        timezone="Europe/Berlin",
    )

    assert len(occurrences) == 4
    for start, end in occurrences:
        assert "T14:00:00" in start
        assert "T15:00:00" in end


def test_naive_timestamps_no_offset():
    """C1: all generated timestamps must be naive (no +XX:XX, no Z)."""
    occurrences = weekly_occurrences(
        start_local="2026-09-07T09:00:00",
        end_local="2026-09-07T10:00:00",
        repeat_until="2026-09-28T23:59:00",
        timezone="America/Denver",
    )
    for start, end in occurrences:
        assert "+" not in start
        assert "Z" not in start
        assert "+" not in end
        assert "Z" not in end
