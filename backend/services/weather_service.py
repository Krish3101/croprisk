import httpx
from typing import Any
from config import settings
from fastapi import HTTPException

async def get_forecast(city: str) -> dict[str, Any]:
    if not settings.OPENWEATHER_KEY:
        raise HTTPException(status_code=500, detail="Weather service configuration missing")

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={settings.OPENWEATHER_KEY}&units=metric"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=502, detail="Weather service temporarily unavailable")

        data = response.json()
        if data.get("cod") != "200":
            raise HTTPException(status_code=502, detail="Forecast data not available")
        
        return data
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Unable to connect to weather service")
