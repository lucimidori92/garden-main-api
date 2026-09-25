"""Watering schedule route."""

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.open_meteo import get_rain_forecast
from app.clients.watering_api import evaluate_plants
from app.database import get_session
from app.models import Plant
from app.schemas import ScheduleItem, ScheduleResponse

router = APIRouter(tags=["Schedule"])
logger = logging.getLogger(__name__)

SessionDep = Annotated[Session, Depends(get_session)]


@router.get(
    "/schedule",
    response_model=ScheduleResponse,
    summary="Get today's watering schedule",
)
def get_schedule(session: SessionDep) -> ScheduleResponse:
    """Builds today's watering schedule for every registered plant.

    Groups plants by city to make one rain forecast call per city, then
    sends the whole batch to the watering-api for a decision on each plant.

    Args:
        session: Database session injected by FastAPI.

    Returns:
        One watering decision per plant.

    Raises:
        HTTPException: 503 if Open-Meteo or the watering-api is unreachable.
    """
    plants = list(session.scalars(select(Plant)))
    if not plants:
        return ScheduleResponse(schedule=[])

    rain_by_city: dict[str, float] = {}
    for plant in plants:
        if plant.city in rain_by_city:
            continue
        logger.info("→ Open-Meteo forecast: %s", plant.city)
        try:
            rain_by_city[plant.city] = get_rain_forecast(
                plant.latitude, plant.longitude
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Open-Meteo is unavailable right now. Please try again shortly.",
            ) from exc

    batch = [
        {
            "plant_id": plant.id,
            "plant_type": plant.plant_type,
            "last_watered_at": plant.last_watered_at.isoformat()
            if plant.last_watered_at
            else None,
            "expected_rain_mm": rain_by_city[plant.city],
        }
        for plant in plants
    ]

    logger.info("→ watering-api POST /evaluations (%d plant(s))", len(batch))
    try:
        decisions = evaluate_plants(batch)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="watering-api is unavailable right now. Please try again shortly.",
        ) from exc

    decisions_by_id = {decision["plant_id"]: decision for decision in decisions}
    schedule = [
        ScheduleItem(
            plant_id=plant.id,
            nickname=plant.nickname,
            plant_type=plant.plant_type,
            city=plant.city,
            expected_rain_mm=rain_by_city[plant.city],
            decision=decisions_by_id[plant.id]["decision"],
            reason=decisions_by_id[plant.id]["reason"],
            next_watering=decisions_by_id[plant.id]["next_watering"],
        )
        for plant in plants
    ]
    return ScheduleResponse(schedule=schedule)
