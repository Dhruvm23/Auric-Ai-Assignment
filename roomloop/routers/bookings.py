from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from roomloop.database import get_db
from roomloop.models import Booking
from roomloop.schemas import (
    BookingCreate,
    BookingOut,
    RecurringBookingCreate,
    RecurringBookingOut,
)
from roomloop.services.booking_service import (
    create_single_booking,
    create_recurring_booking,
    cancel_booking,
    cancel_series,
)

router = APIRouter()


@router.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    try:
        return create_single_booking(
            db,
            room_id=payload.room_id,
            user=payload.user,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/bookings/recurring", response_model=RecurringBookingOut, status_code=201)
def create_recurring(payload: RecurringBookingCreate, db: Session = Depends(get_db)):
    try:
        return create_recurring_booking(
            db,
            room_id=payload.room_id,
            user=payload.user,
            start_time=payload.start_time,
            end_time=payload.end_time,
            repeat_until=payload.repeat_until,
            timezone=payload.timezone,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/bookings", response_model=list[BookingOut])
def list_bookings(
    room_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Booking)
    if room_id is not None:
        q = q.filter(Booking.room_id == room_id)
    if date_from is not None:
        q = q.filter(Booking.start_time >= date_from)
    if date_to is not None:
        q = q.filter(Booking.end_time <= date_to)
    if status is not None:
        q = q.filter(Booking.status == status)
    return q.order_by(Booking.start_time).all()


@router.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.delete("/bookings/{booking_id}", response_model=BookingOut)
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    try:
        return cancel_booking(db, booking_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/series/{series_id}")
def delete_series(series_id: int, db: Session = Depends(get_db)):
    try:
        return cancel_series(db, series_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
