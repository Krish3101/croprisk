import pytest

from app.domain.crops import get_crop, get_stage
from app.domain.engine import (
    ForecastInterval,
    InsufficientForecast,
    compute_digest,
    evaluate,
)


def make_constant_forecast(
    temp_c: float,
    rh: float,
    wind_kmh: float,
    rain_mm: float,
    count: int = 40,
) -> list[ForecastInterval]:
    return [
        ForecastInterval(
            timestamp=f"2026-09-10T{i*3:02d}:00:00Z",
            temperature_c=temp_c,
            relative_humidity=rh,
            wind_kmh=wind_kmh,
            rain_mm=rain_mm,
        )
        for i in range(count)
    ]


# Golden vectors: known inputs with hand-checked expected scores.
def test_golden_vector_1():
    """wheat.anthesis, T=38, RH=40, Wind=5, Rain=0 -> Score=100, HIGH, Extreme Heat."""
    stage = get_stage("wheat", "wheat.anthesis")
    intervals = make_constant_forecast(38.0, 40.0, 5.0, 0.0)
    result = evaluate(intervals, stage)

    assert result.score == 100
    assert result.severity == "HIGH"
    assert result.primary_threat == "Extreme Heat"
    assert round(result.hazard_indices["heat"], 1) == 100.0
    assert round(result.hazard_indices["frost"], 1) == 0.0
    assert round(result.hazard_indices["precip"], 1) == 0.0
    assert round(result.hazard_indices["disease"], 1) == 0.0
    assert round(result.hazard_indices["wind"], 1) == 0.0


def test_golden_vector_2():
    """wheat.anthesis, T=-1, RH=50, Wind=10, Rain=0 -> Score=57, MODERATE, Frost Damage."""
    stage = get_stage("wheat", "wheat.anthesis")
    intervals = make_constant_forecast(-1.0, 50.0, 10.0, 0.0)
    result = evaluate(intervals, stage)

    assert result.score == 57
    assert result.severity == "MODERATE"
    assert result.primary_threat == "Frost Damage"
    assert round(result.hazard_indices["frost"], 1) == 66.7
    assert round(result.hazard_indices["heat"], 1) == 0.0


def test_golden_vector_3():
    """rice.tillering, T=27, RH=90, Wind=10, Rain=0 -> Score=100, HIGH, Fungal Disease Pressure."""
    stage = get_stage("rice", "rice.tillering")
    intervals = make_constant_forecast(27.0, 90.0, 10.0, 0.0)
    result = evaluate(intervals, stage)

    assert result.score == 100
    assert result.severity == "HIGH"
    assert result.primary_threat == "Fungal Disease Pressure"
    assert round(result.hazard_indices["disease"], 1) == 100.0


def test_golden_vector_4():
    """wheat.anthesis, T=20, RH=50, Wind=10, Rain=0 -> Score=0, LOW, None."""
    stage = get_stage("wheat", "wheat.anthesis")
    intervals = make_constant_forecast(20.0, 50.0, 10.0, 0.0)
    result = evaluate(intervals, stage)

    assert result.score == 0
    assert result.severity == "LOW"
    assert result.primary_threat == "None"
    for idx_val in result.hazard_indices.values():
        assert round(idx_val, 1) == 0.0


def test_golden_vector_5():
    """wheat.ripening, T=38, RH=40, Wind=5, Rain=0 -> Score=17, LOW, Extreme Heat."""
    stage = get_stage("wheat", "wheat.ripening")
    intervals = make_constant_forecast(38.0, 40.0, 5.0, 0.0)
    result = evaluate(intervals, stage)

    assert result.score == 17
    assert result.severity == "LOW"
    assert result.primary_threat == "Extreme Heat"
    assert round(result.hazard_indices["heat"], 1) == 60.0


def test_golden_vector_6():
    """cotton.harvest, T=25, RH=90, Wind=55, Rain=3.75 -> Score=65, MODERATE, Excess Precipitation.

    Tests:
    - S_wsum (65.0) beats R_dom (50.0).
    - C_precip == C_wind == 25.0 tie-break resolves to Excess Precipitation.
    - Score 65 pins the top edge of MODERATE.
    """
    stage = get_stage("cotton", "cotton.harvest")
    intervals = make_constant_forecast(25.0, 90.0, 55.0, 3.75)
    result = evaluate(intervals, stage)

    assert result.score == 65
    assert result.severity == "MODERATE"
    assert result.primary_threat == "Excess Precipitation"
    assert round(result.hazard_indices["precip"], 1) == 50.0
    assert round(result.hazard_indices["disease"], 1) == 100.0
    assert round(result.hazard_indices["wind"], 1) == 100.0


def test_empty_intervals_raises():
    stage = get_stage("wheat", "wheat.anthesis")
    with pytest.raises(InsufficientForecast):
        evaluate([], stage)

    crop = get_crop("wheat")
    with pytest.raises(InsufficientForecast):
        compute_digest([], crop)


def test_unknown_crop_raises():
    from app.domain.crops import StageConfig
    bad_stage = StageConfig(
        id="nonexistent.stage",
        name="Bad",
        bbch="00",
        order=1,
        t_crit_heat=30.0,
        t_lethal_heat=40.0,
        t_crit_frost=5.0,
        t_lethal_frost=-5.0,
        r_crit_24h=50.0,
        r_flood_24h=100.0,
        w_crit_lodge=40.0,
        w_severe=80.0,
        weights=(0.2, 0.2, 0.2, 0.2, 0.2),
    )
    intervals = make_constant_forecast(20.0, 50.0, 10.0, 0.0)
    with pytest.raises(ValueError, match="Unknown crop"):
        evaluate(intervals, bad_stage)


def test_hazard_heat_thresholds():
    stage = get_stage("wheat", "wheat.anthesis")
    # Below critical heat (27 C)
    res_below = evaluate(make_constant_forecast(25.0, 40.0, 5.0, 0.0), stage)
    assert res_below.hazard_indices["heat"] == 0.0

    # Mid-range: T=30.5 C for 1 block, rest 20 C (DH = 3.5*3 = 10.5)
    intervals = [
        ForecastInterval("t0", 30.5, 40.0, 5.0, 0.0)
    ] + [ForecastInterval(f"t{i}", 20.0, 40.0, 5.0, 0.0) for i in range(1, 40)]
    res_mid = evaluate(intervals, stage)
    assert 0.0 < res_mid.hazard_indices["heat"] < 100.0

    # Above lethal (34 C) with high DH -> 100.0
    res_lethal = evaluate(make_constant_forecast(35.0, 40.0, 5.0, 0.0), stage)
    assert res_lethal.hazard_indices["heat"] == 100.0


def test_hazard_frost_thresholds():
    stage = get_stage("wheat", "wheat.anthesis")
    # Above critical frost (1 C) -> 0
    res_above = evaluate(make_constant_forecast(5.0, 40.0, 5.0, 0.0), stage)
    assert res_above.hazard_indices["frost"] == 0.0

    # Mid-range: 0 C (t_crit=1, t_lethal=-2) -> (1 - 0) / (1 - (-2)) = 1/3 -> 33.3
    res_mid = evaluate(make_constant_forecast(0.0, 40.0, 5.0, 0.0), stage)
    assert round(res_mid.hazard_indices["frost"], 1) == 33.3

    # At or below lethal (-2 C) -> 100.0
    res_lethal = evaluate(make_constant_forecast(-3.0, 40.0, 5.0, 0.0), stage)
    assert res_lethal.hazard_indices["frost"] == 100.0


def test_hazard_precip_fewer_than_8_blocks():
    stage = get_stage("wheat", "wheat.anthesis")
    # stage: r_crit_24h = 35.0, r_flood_24h = 75.0
    # 5 blocks of 10 mm = 50 mm total
    intervals = [ForecastInterval(f"t{i}", 20.0, 40.0, 5.0, 10.0) for i in range(5)]
    res = evaluate(intervals, stage)
    # (50 - 35) / (75 - 35) = 15 / 40 = 0.375 * 100 = 37.5
    assert round(res.hazard_indices["precip"], 1) == 37.5


def test_hazard_disease_thresholds():
    # wheat disease window: rh_crit=80, t in [15, 25]
    stage = get_stage("wheat", "wheat.anthesis")

    # Run of 3 blocks = 9 hours (< 12 hours) -> I_disease = 0
    intervals_short = [
        ForecastInterval(f"t{i}", 20.0, 85.0, 5.0, 0.0) for i in range(3)
    ] + [ForecastInterval(f"t{i}", 20.0, 70.0, 5.0, 0.0) for i in range(3, 40)]
    res_short = evaluate(intervals_short, stage)
    assert res_short.hazard_indices["disease"] == 0.0

    # Run of 4 blocks = 12 hours -> 30 + 0 = 30.0
    intervals_12h = [
        ForecastInterval(f"t{i}", 20.0, 85.0, 5.0, 0.0) for i in range(4)
    ] + [ForecastInterval(f"t{i}", 20.0, 70.0, 5.0, 0.0) for i in range(4, 40)]
    res_12h = evaluate(intervals_12h, stage)
    assert round(res_12h.hazard_indices["disease"], 1) == 30.0

    # Run of 8 blocks = 24 hours -> 30 + (12/24)*70 = 65.0
    intervals_24h = [
        ForecastInterval(f"t{i}", 20.0, 85.0, 5.0, 0.0) for i in range(8)
    ] + [ForecastInterval(f"t{i}", 20.0, 70.0, 5.0, 0.0) for i in range(8, 40)]
    res_24h = evaluate(intervals_24h, stage)
    assert round(res_24h.hazard_indices["disease"], 1) == 65.0


def test_hazard_wind_thresholds():
    stage = get_stage("wheat", "wheat.anthesis")
    # w_crit_lodge = 40.0, w_severe = 65.0
    # Below critical
    res_below = evaluate(make_constant_forecast(20.0, 40.0, 30.0, 0.0), stage)
    assert res_below.hazard_indices["wind"] == 0.0

    # Mid-range: wind 52.5 -> (52.5 - 40) / (65 - 40) = 12.5 / 25 = 0.5 * 100 = 50.0
    res_mid = evaluate(make_constant_forecast(20.0, 40.0, 52.5, 0.0), stage)
    assert round(res_mid.hazard_indices["wind"], 1) == 50.0

    # Above severe -> 100.0
    res_high = evaluate(make_constant_forecast(20.0, 40.0, 70.0, 0.0), stage)
    assert res_high.hazard_indices["wind"] == 100.0


def test_tie_break_biological_order():
    """Verify tie-break Frost > Heat > Precip > Wind > Disease."""
    # We construct custom stage weights to trigger ties
    from app.domain.crops import StageConfig

    # Tie between Frost and Heat
    stage_tie_frost_heat = StageConfig(
        id="wheat.custom",
        name="Custom",
        bbch="00",
        order=1,
        t_crit_heat=30.0,
        t_lethal_heat=40.0,
        t_crit_frost=5.0,
        t_lethal_frost=-5.0,
        r_crit_24h=50.0,
        r_flood_24h=100.0,
        w_crit_lodge=40.0,
        w_severe=80.0,
        weights=(0.5, 0.5, 0.0, 0.0, 0.0),
    )
    # T=40 (heat 100 -> C=50), min_t=-5 (frost 100 -> C=50)
    intervals = [
        ForecastInterval("t0", 40.0, 40.0, 10.0, 0.0),
        ForecastInterval("t1", -5.0, 40.0, 10.0, 0.0),
    ] + [ForecastInterval(f"t{i}", 20.0, 40.0, 10.0, 0.0) for i in range(2, 40)]
    res = evaluate(intervals, stage_tie_frost_heat)
    # Frost must win over Heat
    assert res.primary_threat == "Frost Damage"


def test_weather_digest_computation():
    crop = get_crop("wheat")
    intervals = [
        ForecastInterval("t0", 35.0, 85.0, 45.0, 12.0),
        ForecastInterval("t1", 18.0, 85.0, 20.0, 8.0),
        ForecastInterval("t2", 20.0, 85.0, 10.0, 0.0),
        ForecastInterval("t3", 22.0, 85.0, 15.0, 0.0),  # 4 consecutive blocks in [15, 25] and RH>=80
        ForecastInterval("t4", 10.0, 50.0, 5.0, 0.0),
    ]
    digest = compute_digest(intervals, crop)
    assert digest.peak_temp_c == 35.0
    assert digest.min_temp_c == 10.0
    assert digest.total_rain_mm == 20.0
    assert digest.max_wind_kmh == 45.0
    assert digest.peak_humidity_pct == 85.0
    # t1, t2, t3 are in [15, 25] with RH 85 (3 blocks = 9 hours; t0 temp is 35 which is > 25)
    assert digest.longest_disease_window_h == 9
