"""Entry point for the garden-main-api."""

from fastapi import FastAPI

app = FastAPI(
    title="garden-main-api",
    description="Smart Garden's main API: plant registration and a watering "
    "schedule based on the Open-Meteo rain forecast.",
    version="0.1.0",
)
