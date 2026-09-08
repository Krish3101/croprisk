from typing import Any

import httpx
from fastapi import HTTPException

from config import settings


async def geocode_location(location: str) -> list[dict[str, Any]]:
    if not settings.OPENWEATHER_KEY:
        raise HTTPException(status_code=500, detail="Weather service configuration missing")

    url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=5&appid={settings.OPENWEATHER_KEY}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Weather service temporarily unavailable")
        return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Unable to connect to weather service")


async def get_forecast(lat: float, lon: float) -> dict[str, Any]:
    if not settings.OPENWEATHER_KEY:
        raise HTTPException(status_code=500, detail="Weather service configuration missing")

    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={settings.OPENWEATHER_KEY}&units=metric"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Location not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=502, detail="Weather service temporarily unavailable")

        data = response.json()
        if data.get("cod") != "200":
            raise HTTPException(status_code=502, detail="Forecast data not available")

        return data
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Unable to connect to weather service")
