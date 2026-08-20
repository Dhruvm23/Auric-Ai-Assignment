from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from roomloop.database import get_db
from roomloop.models import Room
from roomloop.schemas import RoomOut

router = APIRouter()


@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).order_by(Room.id).all()
