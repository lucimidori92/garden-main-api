"""Client for the watering-api's evaluation endpoint."""

from datetime import date
from typing import TypedDict

import httpx

from app.config import WATERING_API_URL

TIMEOUT_SECONDS = 5.0


class PlantBatchItem(TypedDict):
    """One plant sent to the watering-api for evaluation."""

    plant_id: int
    plant_type: str
    last_watered_at: str | None
    """ISO date string (``YYYY-MM-DD``), or ``None`` if never watered."""
    expected_rain_mm: float


class EvaluationOut(TypedDict):
    """One watering decision as returned by the watering-api."""

    plant_id: int
    decision: str
    reason: str
    next_watering: date | None


def evaluate_plants(plants: list[PlantBatchItem]) -> list[EvaluationOut]:
    """Sends a batch of plants to the watering-api for a watering decision.

    Args:
        plants: Plants to evaluate, matching the watering-api's
            ``PlantEvaluation`` schema.

    Returns:
        One decision per plant, in the same order as the request.

    Raises:
        httpx.HTTPError: If the request to the watering-api fails or times out.
    """
    response = httpx.post(
        f"{WATERING_API_URL}/evaluations",
        json={"plants": plants},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()["evaluations"]
