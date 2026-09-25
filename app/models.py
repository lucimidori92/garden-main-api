"""Data models for the garden-main-api."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Plant(Base):
    """A plant registered by the user.

    Attributes:
        id: Auto-incrementing primary key.
        nickname: The name the user gave the plant.
        plant_type: Plant type, matched against the watering-api's rules.
        city: City used to look up coordinates.
        state: State returned by the geocoding lookup, for confirmation.
        latitude: Latitude returned by the geocoding lookup.
        longitude: Longitude returned by the geocoding lookup.
        last_watered_at: Date the plant was last watered, or ``None``.
        created_at: When the plant was registered.
    """

    __tablename__ = "plants"
    __table_args__ = (
        UniqueConstraint("nickname", "plant_type", "city", name="uq_plant_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(100))
    plant_type: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    last_watered_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
