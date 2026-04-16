"""Price Service
Handles market price data retrieval with database caching
"""

import random
from datetime import datetime, timedelta
from typing import Any

import requests
from sqlalchemy import desc
from sqlalchemy.orm import Session

from config import get_logger, settings
from models.database import PriceCache

logger = get_logger(__name__)


def _generate_price_history(base_price: float) -> list[dict[str, Any]]:
    """Generate simulated 7-day price history based on current price
    (Since historical API might not be available)
    """
    history: list[dict[str, Any]] = []
    try:
        base = float(base_price)
        today = datetime.now()

        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime("%d %b")
            # Random fluctuation within ±10%
            price = int(base * (1 + random.uniform(-0.1, 0.1)))
            history.append({"date": date, "price": price})

    except (TypeError, ValueError):
        pass

    return history


def get_market_price(db: Session, commodity: str, state: str = "Maharashtra") -> dict[str, Any]:
    """Get market price for a commodity with caching

    Args:
        db: Database session
        commodity: Crop/commodity name
        state: State name

    Returns:
        Dictionary with price data or error message

    """
    logger.info(f"Fetching price for {commodity} in {state}")

    # 1. Check Cache - use first() to limit results
    cache_entry = (
        db.query(PriceCache)
        .filter(PriceCache.crop == commodity, PriceCache.state == state)
        .order_by(desc(PriceCache.cached_at))
        .first()
    )

    if cache_entry:
        age = datetime.utcnow() - cache_entry.cached_at
        if age.total_seconds() < settings.PRICE_CACHE_TTL:
            logger.info(f"Using cached price data for {commodity}")
            result = {
                "crop": cache_entry.crop,
                "state": cache_entry.state,
                "modal_price": cache_entry.modal_price,
                "min_price": cache_entry.min_price,
                "max_price": cache_entry.max_price,
                "market": "Cached Market",
                "district": "Cached District",
                "arrival_date": datetime.now().strftime("%d-%m-%Y"),
                "unit": cache_entry.unit,
                "cached": True,
            }
            result["history"] = _generate_price_history(result["modal_price"])
            return result
        else:
            logger.info(f"Price cache expired for {commodity}")

    # 2. Call API
    try:
        url = (
            "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
            f"?api-key={settings.INDIA_GOV_API_KEY}"
            "&format=json"
            f"&filters[Commodity]={commodity}"
            f"&filters[State]={state}"
            "&limit=1"
        )

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            if cache_entry:
                return _return_stale_cache(cache_entry)
            return {"error": f"API returned status code {response.status_code}"}

        data = response.json()

        if "records" in data and len(data.get("records", [])) > 0:
            record = data["records"][0]

            modal_price = float(record.get("modal_price", 0))
            min_price = float(record.get("min_price", 0))
            max_price = float(record.get("max_price", 0))
            market = record.get("market", "Unknown Market")
            district = record.get("district", "Unknown District")
            arrival_date = record.get("arrival_date", datetime.now().strftime("%d-%m-%Y"))

            # 3. Update Cache
            if cache_entry:
                cache_entry.modal_price = modal_price
                cache_entry.min_price = min_price
                cache_entry.max_price = max_price
                cache_entry.cached_at = datetime.utcnow()
            else:
                new_cache = PriceCache(
                    crop=commodity,
                    state=state,
                    modal_price=modal_price,
                    min_price=min_price,
                    max_price=max_price,
                    unit="Quintal",
                )
                db.add(new_cache)

            db.commit()

            result = {
                "crop": commodity,
                "state": state,
                "modal_price": modal_price,
                "min_price": min_price,
                "max_price": max_price,
                "market": market,
                "district": district,
                "arrival_date": arrival_date,
                "unit": "Quintal",
            }
            result["history"] = _generate_price_history(modal_price)
            return result

        else:
            logger.warning(f"No price records found for {commodity}")
            if cache_entry:
                return _return_stale_cache(cache_entry)
            return {"error": "No data found for this commodity"}

    except Exception as e:
        logger.error(f"Price API request failed: {e}")
        if cache_entry:
            return _return_stale_cache(cache_entry)
        return {"error": "Unable to fetch price data"}


def _return_stale_cache(cache_entry: PriceCache) -> dict[str, Any]:
    """Return stale cache data when API fails"""
    logger.warning(f"Returning stale price cache for {cache_entry.crop}")
    result = {
        "crop": cache_entry.crop,
        "state": cache_entry.state,
        "modal_price": cache_entry.modal_price,
        "min_price": cache_entry.min_price,
        "max_price": cache_entry.max_price,
        "market": "Stale Cache Market",
        "district": "Stale Cache District",
        "arrival_date": datetime.now().strftime("%d-%m-%Y"),
        "unit": cache_entry.unit,
        "cached": True,
        "stale": True,
    }
    result["history"] = _generate_price_history(result["modal_price"])
    return result
