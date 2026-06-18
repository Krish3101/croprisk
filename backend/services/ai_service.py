"""AI Service
Handles LLM communication, intent detection, query processing, and response formatting
"""

from typing import Any

import httpx
from sqlalchemy.orm import Session

from config import get_logger, get_openrouter_headers, settings
from services.expense_service import get_summary
from services.price_service import get_market_price
from services.soil_service import get_soil_report
from services.weather_service import get_weather

logger = get_logger(__name__)


# ==================== LLM COMMUNICATION ====================


import json

async def ask_llm(prompt: str) -> str:
    """Send a prompt to the LLM and get a response

    Args:
        prompt: The prompt to send to the LLM

    Returns:
        str: LLM response text

    Raises:
        Exception if LLM fails
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    data = {
        "model": settings.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are KisanAI, a helpful farming assistant. Keep answers short, clear, and farmer-friendly.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    headers = get_openrouter_headers()
    if not headers:
        logger.warning("No LLM API key configured")
        raise ValueError("No LLM API key configured")

    logger.info("Sending request to LLM")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=settings.LLM_TIMEOUT)

    if response.status_code != 200:
        logger.warning(f"LLM API returned status {response.status_code}: {response.text[:200]}")
        raise ValueError(f"LLM API returned status {response.status_code}")

    result = response.json()

    if "error" in result:
        error_msg = result.get("error", {})
        if isinstance(error_msg, dict):
            error_msg = error_msg.get("message", str(error_msg))
        logger.error(f"LLM API error: {error_msg}")
        raise ValueError(f"LLM API error: {error_msg}")

    if "choices" not in result or len(result["choices"]) == 0:
        logger.error("LLM API returned no choices")
        raise ValueError("LLM API returned no choices")

    response_text = result["choices"][0]["message"]["content"]
    logger.info("Successfully received LLM response")
    return response_text




# ==================== INTENT DETECTION & QUERY PROCESSING ====================






async def extract_query_info(question: str) -> dict[str, str]:
    """Extract intent, city, and crop in a single structured LLM call"""
    prompt = f"""
    Analyze this question: "{question}"
    Return ONLY a JSON object with these exact keys:
    "intent": one of [weather, price, soil, finance, crop_advice, general]
    "city": extracted city or "Pune" if none
    "crop": extracted crop or "Tomato" if none
    """
    response_text = await ask_llm(prompt)
    try:
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception:
        logger.error(f"Failed to parse JSON from LLM: {response_text}")
        return {"intent": "general", "city": "Pune", "crop": "Tomato"}


def format_weather(city: str, data: dict[str, Any]) -> str:
    """Format weather data for display"""
    temp = data.get("temp", data.get("temperature", 25))
    weather = data.get("weather", data.get("condition", "Clear"))
    humidity = data.get("humidity", 50)
    return f"""
🌦 **Weather Update – {city}**
Temperature: **{temp}°C**
Humidity: **{humidity}%**
Sky: **{weather.title()}**

✅ Good time for outdoor farm work if rain chance is low.
"""


def format_price(data: dict[str, Any]) -> str:
    """Format price data for display"""
    crop = data.get("crop") or data.get("commodity") or "Crop"
    state = data.get("state", "State")
    modal_price = data.get("modal_price", "N/A")
    min_price = data.get("min_price", "N/A")
    max_price = data.get("max_price", "N/A")
    market = data.get("market", "N/A")

    return f"""
📈 **Market Price for {crop} – {state}**
Market: **{market}**
Modal: **₹{modal_price}**
Min: **₹{min_price}**
Max: **₹{max_price}**

✅ Compare local mandi rates to get best deal.
"""


def format_soil(data: dict[str, Any]) -> str:
    """Format soil data for display"""
    return f"""
🧪 **Soil Report**
Soil Type: **{data.get("soil_type", "N/A")}**
pH: **{data.get("ph", "N/A")}**
Moisture: **{data.get("moisture", "N/A")}**
N: **{data.get("nitrogen", "N/A")}**
P: **{data.get("phosphorus", "N/A")}**
K: **{data.get("potassium", "N/A")}**
Last Tested: **{data.get("last_tested", "N/A")}**

✅ Soil looks healthy. Moderate fertilization recommended.
"""


def format_finance(data: dict[str, Any]) -> str:
    """Format financial data for display"""
    income = data.get("total_income") or data.get("income") or 0
    expense = data.get("total_expense") or data.get("expense") or 0
    profit = data.get("profit") or (income - expense)
    return f"""
💰 **Farm Finance Summary**
Income: **₹{income}**
Expenses: **₹{expense}**
Profit: **₹{profit}**

✅ Track weekly to avoid losses.
"""


async def process_query(question: str, db: Session, user_id: int) -> dict[str, str]:
    """Process a user query and return formatted answer

    Args:
        question: User's question
        db: Database session
        user_id: User ID

    Returns:
        Dictionary with 'answer' key containing formatted response

    """
    logger.info(f"Processing query: {question}")

    try:
        info = await extract_query_info(question)
        intent = info.get("intent", "general").lower()
        logger.info(f"Detected intent: {intent}")

        # WEATHER
        if "weather" in intent:
            city = info.get("city", "Pune")
            data = get_weather(db, city)
            if "error" in data:
                return {"answer": data["error"]}
            return {"answer": format_weather(city, data)}

        # PRICE
        if "price" in intent:
            crop = info.get("crop", "Tomato")
            state = getattr(settings, "DEFAULT_STATE", "Maharashtra")
            data = get_market_price(db, crop, state)
            if "error" in data:
                return {"answer": data["error"]}
            return {"answer": format_price(data)}

        # SOIL
        if "soil" in intent:
            data = get_soil_report(db, user_id, "default")
            if "error" in data:
                return {"answer": data["error"]}
            return {"answer": format_soil(data)}

        # FINANCE
        if "finance" in intent:
            data = get_summary(db, user_id)
            return {"answer": format_finance(data)}

        # CROP ADVICE
        if "crop_advice" in intent:
            response = await ask_llm(
                f"Give practical crop advice for a farmer: {question}. Keep it short and in simple language."
            )
            return {"answer": response}

        # GENERAL → fallback to LLM
        response = await ask_llm(f"You are KisanAI. Explain answer simply for farmers: {question}")
        return {"answer": response}
    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        return {"answer": "Sorry, I am currently offline or encountered an error processing your question."}


async def generate_dashboard_insight(weather: str, prices: str) -> str:
    """Generate a quick farming tip based on current data

    Args:
        weather: Weather summary string
        prices: Price summary string

    Returns:
        str: AI-generated insight

    """
    prompt = f"""
    Generate a 1-sentence farming tip based on this data:
    Weather: {weather}
    Prices: {prices}
    
    Keep it practical and actionable for an Indian farmer.
    """

    return await ask_llm(prompt)


__all__ = ["process_query", "generate_dashboard_insight", "ask_llm"]
