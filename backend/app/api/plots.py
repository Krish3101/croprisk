"""Plot routes: list, create, update, delete, and the risk assessment for one plot."""

import datetime
from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import NotFoundError, ValidationError
from app.models import Plot, RiskAssessment
from app.schemas import (
    CropRef,
    LatestRiskSummary,
    PlotCreateRequest,
    PlotRiskResponse,
    PlotSummary,
    PlotUpdateRequest,
    StageRef,
)
from app.services.assessment import (
    CACHE_TTL,
    STALE_SERVE_CAP,
    forecast_age,
    get_plot_risk,
    is_row_relevant,
    location_key,
    preview_score,
)
from app.services.catalogue_loader import get_crop, get_stage

router = APIRouter(prefix="/plots", tags=["plots"])

PlotId = Annotated[int, Path(gt=0, le=2**63 - 1)]


def _get_plot(db: Session, plot_id: int) -> Plot:
    plot = db.query(Plot).filter(Plot.id == plot_id).first()
    if not plot:
        raise NotFoundError(f"Plot {plot_id} not found.")
    return plot


def _check_crop_and_stage(crop_id: str, stage_id: str) -> None:
    if not get_crop(crop_id):
        raise ValidationError(
            "Selected crop does not exist.",
            fields={"crop_id": "Selected crop does not exist."},
        )
    if not get_stage(crop_id, stage_id):
        raise ValidationError(
            "Selected stage does not belong to the crop.",
            fields={"stage_id": "Selected stage does not belong to the crop."},
        )


def _summary(row: RiskAssessment, is_stale: bool) -> LatestRiskSummary:
    return LatestRiskSummary(
        score=row.score,
        severity=row.severity,
        primary_threat=row.primary_threat,
        created_at=row.created_at,
        is_stale=is_stale,
    )


def _latest_risk(plot: Plot, row: RiskAssessment | None) -> LatestRiskSummary | None:
    if row is None or get_stage(plot.crop_id, plot.stage_id) is None:
        return None
    now = datetime.datetime.now(UTC)
    same_place = row.location_key == location_key(plot.latitude, plot.longitude)
    if same_place and forecast_age(row, now) < CACHE_TTL:
        if is_row_relevant(row, plot):
            return _summary(row, is_stale=False)
        # Stage or catalogue changed: score in memory only. The list never shows the advisory,
        # so the LLM call (and the saved re-score) waits for the risk route.
        result = preview_score(plot, row)
        return LatestRiskSummary(
            score=result.score,
            severity=result.severity,
            primary_threat=result.primary_threat,
            created_at=row.created_at,
            is_stale=False,
        )
    # An old forecast for the same place and stage is still worth showing, marked stale,
    # but not past the same 48 h cap the risk route uses.
    if is_row_relevant(row, plot) and forecast_age(row, now) <= STALE_SERVE_CAP:
        return _summary(row, is_stale=True)
    return None


def _to_plot_summary(plot: Plot, row: RiskAssessment | None) -> PlotSummary:
    crop = get_crop(plot.crop_id)
    stage = get_stage(plot.crop_id, plot.stage_id)
    return PlotSummary(
        id=plot.id,
        name=plot.name,
        crop=CropRef(id=plot.crop_id, common_name=crop.common_name if crop else plot.crop_id),
        stage=StageRef(
            id=plot.stage_id,
            name=stage.name if stage else plot.stage_id,
            bbch=stage.bbch if stage else "",
        ),
        location_name=plot.location_name,
        latitude=plot.latitude,
        longitude=plot.longitude,
        sowing_date=plot.sowing_date.isoformat(),
        days_after_sowing=max(0, (datetime.date.today() - plot.sowing_date).days),
        latest_risk=_latest_risk(plot, row),
    )


@router.get("", response_model=list[PlotSummary])
def list_plots(db: Session = Depends(get_db)) -> list[PlotSummary]:
    # Single user with a handful of fields, so one query per plot is fine here.
    summaries = [_to_plot_summary(plot, plot.risk_assessment) for plot in db.query(Plot)]
    # Highest risk first, unassessed last, then by name.
    summaries.sort(key=lambda s: (-(s.latest_risk.score if s.latest_risk else -1), s.name))
    return summaries


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PlotSummary)
def create_plot(req: PlotCreateRequest, db: Session = Depends(get_db)) -> PlotSummary:
    _check_crop_and_stage(req.crop_id, req.stage_id)
    now_iso = datetime.datetime.now(UTC).isoformat()
    plot = Plot(**req.model_dump(), created_at=now_iso, updated_at=now_iso)
    db.add(plot)
    db.commit()
    db.refresh(plot)
    return _to_plot_summary(plot, None)


@router.patch("/{plot_id}", response_model=PlotSummary)
def update_plot(
    req: PlotUpdateRequest,
    plot_id: PlotId,
    db: Session = Depends(get_db),
) -> PlotSummary:
    plot = _get_plot(db, plot_id)
    changes = req.model_dump(exclude_unset=True)
    if changes:
        _check_crop_and_stage(
            changes.get("crop_id", plot.crop_id), changes.get("stage_id", plot.stage_id)
        )
        for field, value in changes.items():
            setattr(plot, field, value)
        plot.updated_at = datetime.datetime.now(UTC).isoformat()
        db.commit()
        db.refresh(plot)
    return _to_plot_summary(plot, plot.risk_assessment)


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot(plot_id: PlotId, db: Session = Depends(get_db)) -> None:
    db.delete(_get_plot(db, plot_id))
    db.commit()


@router.get("/{plot_id}/risk", response_model=PlotRiskResponse)
def get_risk(plot_id: PlotId, db: Session = Depends(get_db)) -> PlotRiskResponse:
    return PlotRiskResponse(**get_plot_risk(_get_plot(db, plot_id), db))


@router.post("/{plot_id}/risk/refresh", response_model=PlotRiskResponse)
def refresh_risk(plot_id: PlotId, db: Session = Depends(get_db)) -> PlotRiskResponse:
    """Fetch a new forecast unless the last one is under 10 minutes old (refreshed=false)."""
    return PlotRiskResponse(**get_plot_risk(_get_plot(db, plot_id), db, force=True))
