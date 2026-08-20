from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from roomloop.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    capacity = Column(Integer, nullable=False)

    bookings = relationship("Booking", back_populates="room")
    series = relationship("Series", back_populates="room")


class Series(Base):
    __tablename__ = "series"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user = Column(String, nullable=False)
    start_time_local = Column(String, nullable=False)
    end_time_local = Column(String, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    repeat_until = Column(String, nullable=False)
    timezone = Column(String, nullable=False)

    room = relationship("Room", back_populates="series")
    bookings = relationship("Booking", back_populates="series")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user = Column(String, nullable=False)
    start_time = Column(String, nullable=False, index=True)
    end_time = Column(String, nullable=False)
    series_id = Column(Integer, ForeignKey("series.id"), nullable=True)
    status = Column(String, nullable=False, default="active")

    room = relationship("Room", back_populates="bookings")
    series = relationship("Series", back_populates="bookings")
