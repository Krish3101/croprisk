"""Advisory service: bypass, LLM generation with schema validation & retry, and deterministic fallback."""

import json
import logging

import httpx

from app.config import settings
from app.domain.crops import CropConfig, StageConfig
from app.domain.engine import AssessmentResult, WeatherDigest
from app.schemas import Action, Advisory, AdvisoryResponse
from app.services.advice_data import get_fallback_advisory

logger = logging.getLogger("croprisk")

SYSTEM_PROMPT = """You are CropRisk's agronomic advisor. You write short, practical guidance for smallholder farmers.

1. GROUND TRUTH: the risk score, severity band and primary threat you are given are already calculated and correct. Never recalculate or dispute them.
2. STAGE SPECIFICITY: explain the damage mechanism for the exact crop and growth stage given (pollen sterility at anthesis, lodging at ripening, root anoxia at seedling, and so on).
3. NO CHEMICAL PRESCRIPTIONS: never name a pesticide, herbicide or fungicide, and never give a dose. Recommend cultural, mechanical, irrigation or biological measures, or advise consulting the local extension officer.
4. ACTIONABLE: assume hand tools, furrow or sprinkler irrigation, family labour.
5. BRIEF: this is read on a phone during a weather emergency. No preamble.
Produce valid JSON matching this schema:
{
  "headline": "...",
  "impact_analysis": "...",
  "actions": [{"timeframe": "immediate_24h"|"preventative_72h", "directive": "..."}],
  "monitoring_focus": "..."
}"""

BYPASS_ADVISORY = Advisory(
    headline="Weather conditions are within normal crop tolerance",
    impact_analysis="Forecasted environmental metrics remain within safe developmental boundaries for this growth stage. No immediate yield-limiting stress is anticipated over the 5-day horizon.",
    actions=[
        Action(
            timeframe="preventative_72h",
            directive="Maintain standard agronomic monitoring and proceed with regular field operations.",
        )
    ],
    monitoring_focus="Conduct routine scouting for baseline soil moisture and standard pest emergence.",
)


def _call_openrouter(user_facts_json: str) -> Advisory | None:
    """Call OpenRouter API once with 8s timeout and validate against Advisory schema."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_facts_json},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.warning("OpenRouter returned status %s: %s", resp.status_code, resp.text)
                return None
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed_advisory = Advisory.model_validate_json(content)
            return parsed_advisory
    except Exception as exc:
        logger.warning("OpenRouter call or validation failed: %s", exc)
        return None


def build_advisory(
    result: AssessmentResult,
    crop: CropConfig,
    stage: StageConfig,
    location_name: str,
    days_after_sowing: int,
    digest: WeatherDigest,
) -> AdvisoryResponse:
    """Produce advisory using bypass (<30), LLM (>=30 with key), or fallback."""
    # 1. Bypass when score < 30
    if result.score < 30:
        return AdvisoryResponse(
            headline=BYPASS_ADVISORY.headline,
            impact_analysis=BYPASS_ADVISORY.impact_analysis,
            actions=BYPASS_ADVISORY.actions,
            monitoring_focus=BYPASS_ADVISORY.monitoring_focus,
            source="bypass",
        )

    # 2. LLM path when score >= 30 and OPENROUTER_API_KEY is present
    if settings.OPENROUTER_API_KEY:
        user_facts = {
            "crop": {
                "common_name": crop.common_name,
                "scientific_name": crop.scientific_name,
            },
            "stage": {
                "id": stage.id,
                "name": stage.name,
                "bbch": stage.bbch,
                "heat_threshold_c": stage.t_crit_heat,
                "frost_threshold_c": stage.t_crit_frost,
            },
            "field": {
                "location": location_name,
                "days_after_sowing": days_after_sowing,
            },
            "assessment": {
                "score": result.score,
                "severity": result.severity,
                "primary_threat": result.primary_threat,
                "hazard_indices": {
                    k: round(v, 1) for k, v in result.hazard_indices.items()
                },
            },
            "weather_digest": {
                "peak_temperature_c": digest.peak_temp_c,
                "min_temperature_c": digest.min_temp_c,
                "total_rain_mm": digest.total_rain_mm,
                "max_wind_kmh": digest.max_wind_kmh,
                "peak_humidity_pct": digest.peak_humidity_pct,
                "longest_disease_window_h": digest.longest_disease_window_h,
            },
        }
        user_facts_json = json.dumps(user_facts)

        # Attempt 1
        llm_advisory = _call_openrouter(user_facts_json)
        # Attempt 2 (retry once on failure)
        if llm_advisory is None:
            logger.info("Retrying OpenRouter call once...")
            llm_advisory = _call_openrouter(user_facts_json)

        if llm_advisory is not None:
            return AdvisoryResponse(
                headline=llm_advisory.headline,
                impact_analysis=llm_advisory.impact_analysis,
                actions=llm_advisory.actions,
                monitoring_focus=llm_advisory.monitoring_focus,
                source="llm",
            )

    # 3. Deterministic fallback
    fallback = get_fallback_advisory(crop.id, result.primary_threat)
    return AdvisoryResponse(
        headline=fallback.headline,
        impact_analysis=fallback.impact_analysis,
        actions=fallback.actions,
        monitoring_focus=fallback.monitoring_focus,
        source="fallback",
    )
