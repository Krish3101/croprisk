"""Pure risk engine for CropRisk. No database, no network, no framework imports."""

import math
from dataclasses import dataclass
from enum import StrEnum

from app.catalogue import CropConfig, StageConfig

INTERVAL_HOURS: int = 3
INTERVALS_PER_24H: int = 8  # 24 hours / 3 hours per interval
DEGREE_HOURS_SCALE: float = 36.0  # Normalisation base for cumulative degree-hours above critical
HEAT_PEAK_WEIGHT: float = 70.0  # Weight given to peak temperature delta
HEAT_DURATION_WEIGHT: float = 30.0  # Weight given to accumulated degree-hours
DISEASE_MIN_RUN_HOURS: int = 12  # Minimum consecutive hours within disease envelope to trigger risk
DISEASE_RAMP_HOURS: float = 24.0  # Additional hours above threshold to reach maximum scaling
DISEASE_BASE_SCORE: float = 30.0  # Base disease score once minimum run is crossed
DISEASE_SCALE: float = 70.0  # Scaling multiplier for disease duration ramp

SEVERITY_LOW_MAX: int = 29
SEVERITY_MODERATE_MAX: int = 65


class Hazard(StrEnum):
    NONE = "None"
    FROST = "Frost Damage"
    HEAT = "Extreme Heat"
    PRECIP = "Excess Precipitation"
    WIND = "Wind Lodging"
    DISEASE = "Fungal Disease Pressure"


class Severity(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class InsufficientForecast(Exception):
    """Raised when the forecast interval list is empty or insufficient."""


@dataclass(frozen=True)
class ForecastInterval:
    timestamp: str
    temperature_c: float
    relative_humidity: float
    wind_kmh: float
    rain_mm: float


@dataclass(frozen=True)
class WeatherDigest:
    peak_temp_c: float
    min_temp_c: float
    total_rain_mm: float
    max_wind_kmh: float
    peak_humidity_pct: float
    longest_disease_window_h: int


@dataclass(frozen=True)
class AssessmentResult:
    score: int
    severity: str
    primary_hazard: str
    hazard_indices: dict[str, float]


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def _round_half_up(n: float) -> int:
    return math.floor(round(n, 9) + 0.5)


def _compute_longest_run_hours(
    intervals: list[ForecastInterval],
    rh_crit: float,
    t_min_dis: float,
    t_max_dis: float,
) -> int:
    longest_run = 0
    current_run = 0
    for interval in intervals:
        matches = (
            interval.relative_humidity >= rh_crit
            and t_min_dis <= interval.temperature_c <= t_max_dis
        )
        if matches:
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    return longest_run * INTERVAL_HOURS


def compute_digest(
    intervals: list[ForecastInterval],
    crop: CropConfig,
) -> WeatherDigest:
    if not intervals:
        raise InsufficientForecast("Forecast intervals cannot be empty.")

    peak_temp = max(i.temperature_c for i in intervals)
    min_temp = min(i.temperature_c for i in intervals)
    total_rain = round(sum(i.rain_mm for i in intervals), 1)
    max_wind = max(i.wind_kmh for i in intervals)
    peak_rh = max(i.relative_humidity for i in intervals)
    disease_hours = _compute_longest_run_hours(
        intervals, crop.rh_crit, crop.t_min_dis, crop.t_max_dis
    )

    return WeatherDigest(
        peak_temp_c=round(peak_temp, 1),
        min_temp_c=round(min_temp, 1),
        total_rain_mm=round(total_rain, 1),
        max_wind_kmh=round(max_wind, 1),
        peak_humidity_pct=round(peak_rh, 1),
        longest_disease_window_h=disease_hours,
    )


def score_forecast(
    intervals: list[ForecastInterval],
    stage: StageConfig,
    crop: CropConfig,
) -> AssessmentResult:
    """Evaluate crop risk against normalised weather intervals.

    Pure function: same inputs -> same outputs, always.
    """
    if not intervals:
        raise InsufficientForecast("Forecast intervals cannot be empty.")

    # 1. Heat
    delta_t_peak = max(0.0, max(i.temperature_c - stage.t_crit_heat for i in intervals))
    dh = sum(max(0.0, i.temperature_c - stage.t_crit_heat) * INTERVAL_HOURS for i in intervals)
    i_heat = (
        _clamp01(delta_t_peak / (stage.t_lethal_heat - stage.t_crit_heat)) * HEAT_PEAK_WEIGHT
        + _clamp01(dh / DEGREE_HOURS_SCALE) * HEAT_DURATION_WEIGHT
    )

    # 2. Frost
    min_t = min(i.temperature_c for i in intervals)
    i_frost = (
        _clamp01((stage.t_crit_frost - min_t) / (stage.t_crit_frost - stage.t_lethal_frost)) * 100.0
    )

    # 3. Excess precipitation (rolling 24-hour window)
    rain_values = [i.rain_mm for i in intervals]
    if len(rain_values) < INTERVALS_PER_24H:
        r24_max = sum(rain_values)
    else:
        r24_max = max(
            sum(rain_values[k : k + INTERVALS_PER_24H])
            for k in range(len(rain_values) - (INTERVALS_PER_24H - 1))
        )
    i_precip = (
        _clamp01((r24_max - stage.r_crit_24h) / (stage.r_flood_24h - stage.r_crit_24h)) * 100.0
    )

    # 4. Fungal disease (consecutive run hours within microclimate envelope)
    l_hours = _compute_longest_run_hours(intervals, crop.rh_crit, crop.t_min_dis, crop.t_max_dis)
    i_disease = (
        0.0
        if l_hours < DISEASE_MIN_RUN_HOURS
        else min(
            100.0,
            DISEASE_BASE_SCORE
            + ((l_hours - DISEASE_MIN_RUN_HOURS) / DISEASE_RAMP_HOURS) * DISEASE_SCALE,
        )
    )

    # 5. Wind lodging
    max_w = max(i.wind_kmh for i in intervals)
    i_wind = _clamp01((max_w - stage.w_crit_lodge) / (stage.w_severe - stage.w_crit_lodge)) * 100.0

    # Score, Severity, Primary Hazard
    w_heat, w_frost, w_precip, w_disease, w_wind = stage.weights
    c_heat = w_heat * i_heat
    c_frost = w_frost * i_frost
    c_precip = w_precip * i_precip
    c_disease = w_disease * i_disease
    c_wind = w_wind * i_wind

    s_wsum = c_heat + c_frost + c_precip + c_disease + c_wind
    w_max = max(stage.weights)
    max_c = max(c_heat, c_frost, c_precip, c_disease, c_wind)
    r_dom = max_c / w_max if w_max > 0 else 0.0

    score = _round_half_up(min(100.0, max(s_wsum, r_dom)))

    if score <= SEVERITY_LOW_MAX:
        severity = Severity.LOW.value
    elif score <= SEVERITY_MODERATE_MAX:
        severity = Severity.MODERATE.value
    else:
        severity = Severity.HIGH.value

    # Biological tie-break order: Frost (5) > Heat (4) > Precip (3) > Wind (2) > Disease (1)
    if max_c == 0.0:
        primary_hazard = Hazard.NONE.value
    else:
        candidates = [
            (c_frost, 5, Hazard.FROST.value),
            (c_heat, 4, Hazard.HEAT.value),
            (c_precip, 3, Hazard.PRECIP.value),
            (c_wind, 2, Hazard.WIND.value),
            (c_disease, 1, Hazard.DISEASE.value),
        ]
        _, _, primary_hazard = max(candidates, key=lambda item: (item[0], item[1]))

    return AssessmentResult(
        score=score,
        severity=severity,
        primary_hazard=primary_hazard,
        hazard_indices={
            "heat": i_heat,
            "frost": i_frost,
            "precip": i_precip,
            "disease": i_disease,
            "wind": i_wind,
        },
    )
