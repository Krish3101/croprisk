import httpx
import json
from config import settings
from fastapi import HTTPException

async def ask_llm(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    data = {
        "model": settings.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are KisanAI Risk Intelligence, an expert agronomist.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="No LLM API key configured")
        
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kisanai.com",
        "X-Title": "KisanAI Risk Intelligence"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers, timeout=30)
            
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"LLM API failed: {response.status_code}")
            
        result = response.json()
        if "error" in result:
            raise HTTPException(status_code=502, detail="LLM API returned an error")
            
        return result["choices"][0]["message"]["content"]
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Failed to connect to LLM service")

async def explain_risk(crop: str, stage: str, score: int, severity: str, primary_risk: str, weather_summary: str) -> dict:
    prompt = f"""
    Evaluate the risk for a {crop} crop at the {stage} stage given this weather forecast: {weather_summary}.
    The calculated deterministic risk score is {score}/100.
    The severity is {severity}.
    The primary risk factor identified is: {primary_risk}.
    
    Return ONLY a strict JSON object with these exact keys:
    "analysis": A 2-sentence explanation of why this weather poses this risk to this crop at this stage.
    "recommendation": A 1-sentence actionable recommendation for the farmer.
    """
    
    try:
        response_text = await ask_llm(prompt)
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception:
        return {
            "analysis": f"Weather conditions indicate a {severity} risk of {primary_risk}.",
            "recommendation": "Monitor the crop closely and take preventative measures."
        }
