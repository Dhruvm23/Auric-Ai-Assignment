"""Seed the database with rooms from the facilities dashboard sample (C2)."""

from roomloop.database import SessionLocal
from roomloop.models import Room

ROOMS = [
    {"id": 3, "name": "Aurora", "capacity": 8},
    {"id": 4, "name": "Basalt", "capacity": 4},
    {"id": 9, "name": "Cinder", "capacity": 12},
    {"id": 17, "name": "Dune", "capacity": 6},
]


def seed_rooms():
    db = SessionLocal()
    try:
        if db.query(Room).count() > 0:
            return
        for r in ROOMS:
            db.add(Room(**r))
        db.commit()
    finally:
        db.close()
