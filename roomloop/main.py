from contextlib import asynccontextmanager
from fastapi import FastAPI
from roomloop.database import init_db
from roomloop.routers import rooms, bookings
from roomloop.seed import seed_rooms


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_rooms()
    yield


app = FastAPI(title="RoomLoop", version="1.0.0", lifespan=lifespan)

app.include_router(rooms.router)
app.include_router(bookings.router)
