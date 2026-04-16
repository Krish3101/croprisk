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


async def ask_llm(prompt: str) -> str:
    """Send a prompt to the LLM and get a response

    Args:
        prompt: The prompt to send to the LLM

    Returns:
        str: LLM response text

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

    try:
        headers = get_openrouter_headers()
        if not headers:
            logger.warning("No LLM API key configured, using mock response")
            return _mock_response(prompt)

        logger.info("Sending request to LLM")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers, timeout=settings.LLM_TIMEOUT)

        if response.status_code != 200:
            logger.warning(f"LLM API returned status {response.status_code}: {response.text[:200]}")
            return _mock_response(prompt)

        result = response.json()

        # Check for API errors
        if "error" in result:
            error_msg = result.get("error", {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
            logger.error(f"LLM API error: {error_msg}")
            return _mock_response(prompt)

        if "choices" not in result or len(result["choices"]) == 0:
            logger.error("LLM API returned no choices")
            return _mock_response(prompt)

        response_text = result["choices"][0]["message"]["content"]
        logger.info("Successfully received LLM response")
        return response_text

    except httpx.TimeoutException:
        logger.error(f"LLM request timed out after {settings.LLM_TIMEOUT} seconds")
        return _mock_response(prompt)
    except httpx.RequestError as e:
        logger.error(f"LLM network request failed: {e}")
        return _mock_response(prompt)
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        return _mock_response(prompt)


def _mock_response(prompt: str) -> str:
    """Generate a plausible mock response based on keywords

    Args:
        prompt: The original prompt

    Returns:
        str: Mock response text

    """
    p = prompt.lower()

    if "weather" in p:
        return "The weather looks clear for the next few days. Good for spraying pesticides."

    if "price" in p:
        return "Market prices are fluctuating. It might be good to hold for a week if you have storage."

    if "soil" in p:
        return "Your soil nitrogen levels seem low. Consider adding Urea or compost."

    if "finance" in p:
        return "You are in profit this season! Keep tracking your expenses."

    if "advice" in p or "tip" in p:
        return "Rotate your crops to maintain soil health and reduce pest attacks."

    return "I am in offline mode. Please check your internet or API key for live AI answers. Meanwhile: Farming is essential!"


# ==================== INTENT DETECTION & QUERY PROCESSING ====================


async def detect_intent(question: str) -> str:
    """Detect the intent of a user question

    Args:
        question: User's question

    Returns:
        str: Detected intent (weather, price, soil, finance, crop_advice, general)

    """
    prompt = f"""
    Classify the intent of this question into one word:
    - weather
    - price
    - soil
    - finance
    - crop_advice
    - general

    Question: "{question}"

    ONLY return one word.
    """

    intent = await ask_llm(prompt)
    return intent.strip().lower()


async def extract_city(question: str) -> str:
    """Extract city name from question

    Args:
        question: User's question

    Returns:
        Extracted city name (default: Pune)

    """
    prompt = f"""
    Extract the city name from: "{question}"
    If none found, return "Pune".
    ONLY return the city.
    """
    return (await ask_llm(prompt)).strip()


async def extract_crop(question: str) -> str:
    """Extract crop name from question

    Args:
        question: User's question

    Returns:
        str: Extracted crop name (default: Tomato)

    """
    prompt = f"""
    Extract the crop name from: "{question}"
    ONLY return the crop. If not found, return "Tomato".
    """
    return (await ask_llm(prompt)).strip()


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


async def process_query(question: str, db: Session) -> dict[str, str]:
    """Process a user query and return formatted answer

    Args:
        question: User's question
        db: Database session

    Returns:
        Dictionary with 'answer' key containing formatted response

    """
    logger.info(f"Processing query: {question}")

    intent = await detect_intent(question)
    logger.info(f"Detected intent: {intent}")

    # WEATHER
    if "weather" in intent:
        city = await extract_city(question)
        data = get_weather(db, city)
        if "error" in data:
            return {"answer": data["error"]}
        return {"answer": format_weather(city, data)}

    # PRICE
    if "price" in intent:
        crop = await extract_crop(question)
        state = getattr(settings, "DEFAULT_STATE", "Maharashtra")
        data = get_market_price(db, crop, state)
        if "error" in data:
            return {"answer": data["error"]}
        return {"answer": format_price(data)}

    # SOIL
    if "soil" in intent:
        data = get_soil_report(db, "default")
        if "error" in data:
            return {"answer": data["error"]}
        return {"answer": format_soil(data)}

    # FINANCE
    if "finance" in intent:
        data = get_summary(db)
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
