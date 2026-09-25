"""Plant routes."""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clients.open_meteo import CityNotFoundError, geocode_city
from app.database import get_session
from app.models import Plant
from app.schemas import (
    PlantIn,
    PlantListOut,
    PlantOut,
    PlantUpdate,
    SortField,
    SortOrder,
)

router = APIRouter(prefix="/plants", tags=["Plants"])

SessionDep = Annotated[Session, Depends(get_session)]

SORT_COLUMNS = {
    "nickname": Plant.nickname,
    "plant_type": Plant.plant_type,
    "city": Plant.city,
    "created_at": Plant.created_at,
}


def _geocode_or_error(city: str) -> tuple[str, float, float]:
    """Looks up a city's coordinates, turning lookup failures into HTTP errors.

    Args:
        city: The city name to look up.

    Returns:
        The matched state, latitude and longitude.

    Raises:
        HTTPException: 404 if the city has no match; 503 if Open-Meteo is
            unreachable or times out.
    """
    try:
        result = geocode_city(city)
    except CityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Open-Meteo is unavailable right now. Please try again shortly.",
        ) from exc
    return result.state, result.latitude, result.longitude


@router.post(
    "",
    response_model=PlantOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a plant",
)
def create_plant(plant_in: PlantIn, session: SessionDep) -> Plant:
    """Registers a plant, looking up its city's coordinates on Open-Meteo.

    Args:
        plant_in: The plant to register.
        session: Database session injected by FastAPI.

    Returns:
        The created plant, including its resolved state and coordinates.
    """
    state, latitude, longitude = _geocode_or_error(plant_in.city)
    plant = Plant(
        nickname=plant_in.nickname,
        plant_type=plant_in.plant_type,
        city=plant_in.city,
        state=state,
        latitude=latitude,
        longitude=longitude,
    )
    session.add(plant)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A plant with this nickname, type and city is already registered.",
        ) from exc
    session.refresh(plant)
    return plant


@router.get("", response_model=PlantListOut, summary="List plants")
def list_plants(
    session: SessionDep,
    plant_type: Annotated[str | None, Query()] = None,
    city: Annotated[str | None, Query()] = None,
    sort_by: Annotated[SortField, Query()] = "created_at",
    order: Annotated[SortOrder, Query()] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PlantListOut:
    """Lists plants with optional filters, sorting and pagination.

    Args:
        session: Database session injected by FastAPI.
        plant_type: Only return plants of this type, if given.
        city: Only return plants in this city, if given.
        sort_by: Field to sort by.
        order: Sort direction, ``asc`` or ``desc``.
        page: 1-based page number.
        page_size: Number of items per page.

    Returns:
        The matching plants for the requested page, plus the total count.
    """
    stmt = select(Plant)
    if plant_type is not None:
        stmt = stmt.where(Plant.plant_type == plant_type)
    if city is not None:
        stmt = stmt.where(Plant.city == city)

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    direction = asc if order == "asc" else desc
    stmt = stmt.order_by(direction(SORT_COLUMNS[sort_by]))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    items = list(session.scalars(stmt))
    return PlantListOut(items=items, total=total, page=page, page_size=page_size)


@router.put("/{plant_id}", response_model=PlantOut, summary="Update a plant")
def update_plant(
    plant_id: int, plant_update: PlantUpdate, session: SessionDep
) -> Plant:
    """Updates a plant, re-running geocoding only if its city changed.

    Args:
        plant_id: The plant to update.
        plant_update: The fields to change; unset fields are left as-is.
        session: Database session injected by FastAPI.

    Returns:
        The updated plant.

    Raises:
        HTTPException: 404 if the plant doesn't exist.
    """
    plant = session.get(Plant, plant_id)
    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No plant found with id {plant_id}.",
        )

    data = plant_update.model_dump(exclude_unset=True)

    if "city" in data and data["city"] != plant.city:
        state, latitude, longitude = _geocode_or_error(data["city"])
        plant.state = state
        plant.latitude = latitude
        plant.longitude = longitude

    for field, value in data.items():
        setattr(plant, field, value)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A plant with this nickname, type and city is already registered.",
        ) from exc
    session.refresh(plant)
    return plant


@router.delete(
    "/{plant_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a plant"
)
def delete_plant(plant_id: int, session: SessionDep) -> None:
    """Deletes a plant.

    Args:
        plant_id: The plant to delete.
        session: Database session injected by FastAPI.

    Raises:
        HTTPException: 404 if the plant doesn't exist.
    """
    plant = session.get(Plant, plant_id)
    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No plant found with id {plant_id}.",
        )
    session.delete(plant)
    session.commit()
