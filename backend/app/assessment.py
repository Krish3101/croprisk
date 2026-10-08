"""The risk assessment for one plot: reuse the stored one, or fetch, score and store."""

import datetime
import json
from dataclasses import asdict
from datetime import UTC

import httpx
from fastapi import HTTPException
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app import advisory, weather
from app.catalogue import CropConfig, StageConfig, get_crop, get_stage
from app.engine import (
    AssessmentResult,
    ForecastInterval,
    InsufficientForecast,
    compute_digest,
    score_forecast,
)
from app.models import Assessment, Plot

CACHE_TTL = datetime.timedelta(hours=12)


def as_utc(dt: datetime.datetime) -> datetime.datetime:
    # SQLite keeps no time zone, so stored times come back naive; they were written in UTC
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def location_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.2f}:{longitude:.2f}"


def matches(row: Assessment | None, plot: Plot) -> bool:
    """True when the stored assessment was scored for the plot's current location and stage."""
    return (
        row is not None
        and row.location_key == location_key(plot.latitude, plot.longitude)
        and row.stage_id == plot.stage_id
    )


def is_reusable(row: Assessment | None, plot: Plot, now: datetime.datetime) -> bool:
    """The one caching rule: same location and stage, and a forecast under 12 hours old."""
    return matches(row, plot) and now - as_utc(row.forecast_fetched_at) < CACHE_TTL


def catalogue_entry(plot: Plot) -> tuple[CropConfig, StageConfig]:
    return get_crop(plot.crop_id), get_stage(plot.crop_id, plot.stage_id)


def _days_after_sowing(plot: Plot) -> int:
    return max(0, (datetime.date.today() - plot.sowing_date).days)


def _score(plot: Plot, intervals: list[ForecastInterval], advisory_builder):
    crop, stage = catalogue_entry(plot)
    result: AssessmentResult = score_forecast(intervals, stage, crop)
    digest = compute_digest(intervals, crop)
    adv = advisory_builder(
        result, crop, stage, plot.location_name, _days_after_sowing(plot), digest
    )
    return result, adv


def _store_new_assessment(
    plot: Plot,
    intervals: list[ForecastInterval],
    now: datetime.datetime,
    db: Session,
    advisory_builder,
) -> Assessment:
    result, adv = _score(plot, intervals, advisory_builder)
    values = {
        "location_key": location_key(plot.latitude, plot.longitude),
        "stage_id": plot.stage_id,
        "score": result.score,
        "severity": result.severity,
        "primary_hazard": result.primary_hazard,
        "hazard_indices": json.dumps(result.hazard_indices),
        "forecast": json.dumps([asdict(i) for i in intervals]),
        "forecast_fetched_at": now,
        "advisory": adv.model_dump_json(exclude={"source"}),
        "advisory_source": adv.source,
        "created_at": now,
    }
    # Upsert so a second writer updates the row instead of hitting the primary key.
    stmt = sqlite_insert(Assessment).values(plot_id=plot.id, **values)
    db.execute(stmt.on_conflict_do_update(index_elements=["plot_id"], set_=values))
    db.commit()
    return db.query(Assessment).filter(Assessment.plot_id == plot.id).one()


def build_response(plot: Plot, row: Assessment) -> dict:
    crop, stage = catalogue_entry(plot)
    intervals = [ForecastInterval(**item) for item in json.loads(row.forecast)]
    digest = compute_digest(intervals, crop)
    hazard_indices = {k: round(float(v), 1) for k, v in json.loads(row.hazard_indices).items()}

    return {
        "plot": {
            "id": plot.id,
            "name": plot.name,
            "crop": crop.common_name,
            "crop_id": plot.crop_id,
            "scientific_name": crop.scientific_name,
            "stage": stage.name,
            "stage_id": plot.stage_id,
            "bbch": stage.bbch,
            "location_name": plot.location_name,
            "latitude": plot.latitude,
            "longitude": plot.longitude,
            "sowing_date": plot.sowing_date.isoformat(),
            "days_after_sowing": _days_after_sowing(plot),
        },
        "assessment": {
            "score": row.score,
            "severity": row.severity,
            "primary_hazard": row.primary_hazard,
            "hazard_indices": hazard_indices,
            "created_at": as_utc(row.created_at),
            "forecast_fetched_at": as_utc(row.forecast_fetched_at),
        },
        "advisory": {**json.loads(row.advisory), "source": row.advisory_source},
        "weather": {
            "digest": asdict(digest),
            "intervals": [asdict(i) for i in intervals],
        },
    }


def get_assessment(
    plot: Plot,
    db: Session,
    force: bool = False,
    weather_provider=None,
    advisory_builder=None,
    now: datetime.datetime | None = None,
) -> dict:
    """Reuse the stored assessment if it is still valid, otherwise fetch a new forecast.

    force (the Recalculate button) always fetches.
    """
    weather_provider = weather_provider or weather.fetch_forecast
    advisory_builder = advisory_builder or advisory.build_advisory
    now = now or datetime.datetime.now(UTC)

    row = db.query(Assessment).filter(Assessment.plot_id == plot.id).first()
    if not force and is_reusable(row, plot, now):
        return build_response(plot, row)

    try:
        intervals = weather_provider(plot.latitude, plot.longitude)
    except (HTTPException, InsufficientForecast, httpx.HTTPError) as exc:
        raise HTTPException(503, "Weather service unavailable.") from exc
    new_row = _store_new_assessment(plot, intervals, now, db, advisory_builder)
    return build_response(plot, new_row)
