"""Weather Service
Handles weather data retrieval from OpenWeather API with database caching
"""

from datetime import datetime
from typing import Any

import requests
from sqlalchemy.orm import Session

from config import get_logger, settings
from models.database import WeatherCache

logger = get_logger(__name__)


def get_weather(db: Session, city: str) -> dict[str, Any]:
    """Get weather information for a city with caching

    Args:
        db: Database session
        city: City name

    Returns:
        Dictionary with weather data or error message

    """
    logger.info(f"Fetching weather for city: {city}")

    # 1. Check Cache
    cache_entry = db.query(WeatherCache).filter(WeatherCache.city == city).first()

    if cache_entry:
        # Check if cache is valid (not expired)
        age = datetime.utcnow() - cache_entry.cached_at
        if age.total_seconds() < settings.WEATHER_CACHE_TTL:
            logger.info(f"Using cached weather data for {city}")
            return {
                "city": cache_entry.city,
                "temp": cache_entry.temperature,
                "temperature": cache_entry.temperature,  # Alias for compatibility
                "condition": cache_entry.condition,
                "weather": cache_entry.condition,  # Alias for compatibility
                "humidity": cache_entry.humidity,
                "wind_speed": cache_entry.wind_speed,
                "cached": True,
            }
        else:
            logger.info(f"Weather cache expired for {city}")

    # 2. Call API
    if not settings.OPENWEATHER_KEY:
        logger.warning("OpenWeather API key not configured")
        return {"error": "Weather service configuration missing"}

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={settings.OPENWEATHER_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        
        # Handle various HTTP status codes
        if response.status_code == 404:
            logger.warning(f"City not found: {city}")
            return {"error": f"City '{city}' not found"}
        
        if response.status_code == 401:
            logger.error("Invalid OpenWeather API key")
            return {"error": "Weather service authentication failed"}
        
        data = response.json()

        if data.get("cod") != 200:
            logger.warning(f"Weather API error for {city}: {data.get('message')}")
            return {"error": data.get("message", "Weather data not available")}

        # Extract data - using standardized field names
        weather_data = {
            "city": data.get("name", city),
            "temp": data.get("main", {}).get("temp", 0),
            "temperature": data.get("main", {}).get("temp", 0),  # Alias for compatibility
            "humidity": data.get("main", {}).get("humidity", 0),
            "condition": data.get("weather", [{}])[0].get("description", "Unknown"),
            "weather": data.get("weather", [{}])[0].get("description", "Unknown"),  # Alias for compatibility
            "wind_speed": data.get("wind", {}).get("speed", 0),
        }

        # 3. Update Cache
        if cache_entry:
            # Update existing
            cache_entry.temperature = weather_data["temp"]
            cache_entry.humidity = weather_data["humidity"]
            cache_entry.condition = weather_data["condition"]
            cache_entry.wind_speed = weather_data["wind_speed"]
            cache_entry.cached_at = datetime.utcnow()
        else:
            # Create new
            new_cache = WeatherCache(
                city=city,
                temperature=weather_data["temp"],
                humidity=weather_data["humidity"],
                condition=weather_data["condition"],
                wind_speed=weather_data["wind_speed"],
            )
            db.add(new_cache)

        db.commit()

        logger.info(f"Successfully fetched and cached weather for {city}")
        return weather_data

    except requests.Timeout:
        logger.error(f"Weather API request timed out for {city}")
        # If API times out but we have stale cache, return that
        if cache_entry:
            logger.warning(f"Returning stale cache for {city} due to timeout")
            return {
                "city": cache_entry.city,
                "temp": cache_entry.temperature,
                "temperature": cache_entry.temperature,
                "condition": cache_entry.condition,
                "weather": cache_entry.condition,
                "humidity": cache_entry.humidity,
                "wind_speed": cache_entry.wind_speed,
                "cached": True,
                "stale": True,
            }
        return {"error": "Weather service request timed out"}
        
    except requests.RequestException as e:
        logger.error(f"Weather API request failed for {city}: {e}")
        # If API fails but we have stale cache, might be better to return that than error
        if cache_entry:
            logger.warning(f"Returning stale cache for {city} due to API failure")
            return {
                "city": cache_entry.city,
                "temp": cache_entry.temperature,
                "temperature": cache_entry.temperature,
                "condition": cache_entry.condition,
                "weather": cache_entry.condition,
                "humidity": cache_entry.humidity,
                "wind_speed": cache_entry.wind_speed,
                "cached": True,
                "stale": True,
            }
        return {"error": "Unable to connect to weather service"}
        
    except Exception as e:
        logger.error(f"Weather API request failed for {city}: {e}")
        # If API fails but we have stale cache, might be better to return that than error
        if cache_entry:
            logger.warning(f"Returning stale cache for {city} due to API failure")
            return {
                "city": cache_entry.city,
                "temp": cache_entry.temperature,
                "temperature": cache_entry.temperature,  # Alias for compatibility
                "condition": cache_entry.condition,
                "weather": cache_entry.condition,  # Alias for compatibility
                "humidity": cache_entry.humidity,
                "wind_speed": cache_entry.wind_speed,
                "cached": True,
                "stale": True,
            }

        return {"error": "Unable to fetch weather data"}


def get_weather_forecast(db: Session, city: str) -> dict[str, Any]:
    """Get 5-day weather forecast for a city with caching

    Args:
        db: Database session
        city: City name

    Returns:
        Dictionary with forecast data or error message

    """
    from models.database import WeatherForecastCache

    logger.info(f"Fetching weather forecast for city: {city}")

    # 1. Check Cache
    cache_entries = db.query(WeatherForecastCache).filter(WeatherForecastCache.city == city).all()

    if cache_entries:
        # Check if cache is valid (not expired)
        age = datetime.utcnow() - cache_entries[0].cached_at
        if age.total_seconds() < settings.WEATHER_CACHE_TTL:
            logger.info(f"Using cached forecast data for {city}")
            return {
                "city": city,
                "forecast": [
                    {
                        "date": entry.date,
                        "temp": entry.temperature,
                        "temp_min": entry.temp_min,
                        "temp_max": entry.temp_max,
                        "condition": entry.condition,
                        "humidity": entry.humidity,
                    }
                    for entry in cache_entries
                ],
                "cached": True,
            }
        else:
            logger.info(f"Forecast cache expired for {city}")
            # Delete old cache
            for entry in cache_entries:
                db.delete(entry)
            db.commit()

    # 2. Call API
    if not settings.OPENWEATHER_KEY:
        logger.warning("OpenWeather API key not configured")
        return {"error": "Weather service configuration missing"}

    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={settings.OPENWEATHER_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("cod") != "200":
            logger.warning(f"Forecast API error for {city}: {data.get('message')}")
            return {"error": data.get("message", "Forecast data not available")}

        # Parse 5-day forecast (API returns 3-hour intervals, we'll get daily averages)
        forecast_list = data.get("list", [])
        daily_data = {}

        for item in forecast_list:
            # Get date (YYYY-MM-DD)
            dt_txt = item.get("dt_txt", "")
            if not dt_txt:
                continue

            date = dt_txt.split(" ")[0]

            if date not in daily_data:
                daily_data[date] = []

            daily_data[date].append(
                {
                    "temp": item.get("main", {}).get("temp", 0),
                    "temp_min": item.get("main", {}).get("temp_min", 0),
                    "temp_max": item.get("main", {}).get("temp_max", 0),
                    "condition": item.get("weather", [{}])[0].get("description", "Unknown"),
                    "humidity": item.get("main", {}).get("humidity", 0),
                }
            )

        # Calculate daily averages and get 5 days
        forecast_data = []
        for date in sorted(daily_data.keys())[:5]:
            day_items = daily_data[date]
            avg_temp = sum(d["temp"] for d in day_items) / len(day_items)
            min_temp = min(d["temp_min"] for d in day_items)
            max_temp = max(d["temp_max"] for d in day_items)
            avg_humidity = sum(d["humidity"] for d in day_items) / len(day_items)
            # Use the most common condition or the first one
            condition = day_items[len(day_items) // 2]["condition"]

            forecast_data.append(
                {
                    "date": date,
                    "temp": round(avg_temp, 1),
                    "temp_min": round(min_temp, 1),
                    "temp_max": round(max_temp, 1),
                    "condition": condition,
                    "humidity": round(avg_humidity, 1),
                }
            )

            # Cache this day's forecast
            new_cache = WeatherForecastCache(
                city=city,
                date=date,
                temperature=round(avg_temp, 1),
                temp_min=round(min_temp, 1),
                temp_max=round(max_temp, 1),
                condition=condition,
                humidity=round(avg_humidity, 1),
            )
            db.add(new_cache)

        db.commit()

        logger.info(f"Successfully fetched and cached forecast for {city}")
        return {"city": city, "forecast": forecast_data}

    except Exception as e:
        logger.error(f"Forecast API request failed for {city}: {e}")
        return {"error": "Unable to fetch forecast data"}
