"""Client for the Open-Meteo geocoding and forecast APIs."""

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 5.0


class CityNotFoundError(Exception):
    """Raised when Open-Meteo has no match for the given city."""


class GeocodeResult:
    """Coordinates and state returned for a city.

    Attributes:
        city: The city name as matched by Open-Meteo.
        state: The state/region returned for the match, if any.
        latitude: Latitude of the match.
        longitude: Longitude of the match.
    """

    def __init__(
        self, city: str, state: str, latitude: float, longitude: float
    ) -> None:
        """Stores a geocoding match.

        Args:
            city: The city name as matched by Open-Meteo.
            state: The state/region returned for the match, if any.
            latitude: Latitude of the match.
            longitude: Longitude of the match.
        """
        self.city = city
        self.state = state
        self.latitude = latitude
        self.longitude = longitude


def geocode_city(city: str) -> GeocodeResult:
    """Looks up a city's coordinates using Open-Meteo's geocoding API.

    Args:
        city: The city name to look up.

    Returns:
        The matched city's coordinates and state.

    Raises:
        CityNotFoundError: If Open-Meteo has no match for the city.
        httpx.HTTPError: If the request to Open-Meteo fails or times out.
    """
    response = httpx.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "pt"},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        raise CityNotFoundError(f"No match found for city '{city}'.")
    match = results[0]
    return GeocodeResult(
        city=match["name"],
        state=match.get("admin1", ""),
        latitude=match["latitude"],
        longitude=match["longitude"],
    )


def get_rain_forecast(latitude: float, longitude: float) -> float:
    """Looks up the rain expected today and tomorrow for a location.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.

    Returns:
        The total precipitation, in mm, forecast for today and tomorrow.

    Raises:
        httpx.HTTPError: If the request to Open-Meteo fails or times out.
    """
    response = httpx.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "daily": "precipitation_sum",
            "forecast_days": 2,
            "timezone": "America/Sao_Paulo",
        },
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    daily_rain = response.json()["daily"]["precipitation_sum"]
    return sum(daily_rain)
