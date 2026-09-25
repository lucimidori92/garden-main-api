"""Entry point for the garden-main-api."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import plants, schedule

# INFO-level app logs (e.g. the "→ Open-Meteo" / "→ watering-api" call traces
# in app/routers/schedule.py) are otherwise silently dropped: the root logger
# has no handler by default, and Python's "handler of last resort" only
# prints WARNING and above.
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Prepares the database before the API accepts requests.

    Args:
        _app: FastAPI application (unused).

    Yields:
        Control back to FastAPI while the API is running.
    """
    init_db()
    yield


app = FastAPI(
    title="garden-main-api",
    description="Smart Garden's main API: plant registration and a watering "
    "schedule based on the Open-Meteo rain forecast.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(plants.router)
app.include_router(schedule.router)


@app.get("/")
def root() -> dict[str, str]:
    """Greets whoever hits the API root and points them to the docs.

    Returns:
        A welcome message and the interactive docs URL.
    """
    return {"message": "🌱 garden-main-api is running! Docs at /docs."}
