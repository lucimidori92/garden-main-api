"""Request and response schemas for the garden-main-api."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PlantIn(BaseModel):
    """Payload to register a new plant."""

    nickname: str = Field(examples=["Basil on the windowsill"])
    plant_type: str = Field(examples=["herb"])
    city: str = Field(examples=["Campinas"])


class PlantUpdate(BaseModel):
    """Payload to update an existing plant. Unset fields are left unchanged."""

    nickname: str | None = Field(default=None, examples=["Basil on the windowsill"])
    plant_type: str | None = Field(default=None, examples=["herb"])
    city: str | None = Field(default=None, examples=["Campinas"])
    last_watered_at: date | None = Field(default=None, examples=["2026-09-25"])


class PlantOut(BaseModel):
    """A plant as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    plant_type: str
    city: str
    state: str
    latitude: float
    longitude: float
    last_watered_at: date | None
    created_at: datetime


class PlantListOut(BaseModel):
    """A page of plants."""

    items: list[PlantOut]
    total: int
    page: int
    page_size: int


SortField = Literal["nickname", "plant_type", "city", "created_at"]
SortOrder = Literal["asc", "desc"]


class ScheduleItem(BaseModel):
    """A plant combined with its watering decision for today."""

    plant_id: int
    nickname: str
    plant_type: str
    city: str
    expected_rain_mm: float
    decision: str
    reason: str
    next_watering: date | None


class ScheduleResponse(BaseModel):
    """Today's watering schedule for every registered plant."""

    schedule: list[ScheduleItem]
