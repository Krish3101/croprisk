"""The HTTP endpoints: the crop list, place search, plots and their risk assessment."""

import datetime
from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.assessment import as_utc, get_assessment, matches
from app.catalogue import CROPS, get_crop, get_stage
from app.db import get_db
from app.models import Assessment, Plot
from app.schemas import (
    AssessmentResponse,
    CropRef,
    CropSummary,
    GeocodeCandidate,
    LatestAssessment,
    PlotRequest,
    PlotSummary,
    StageRef,
    StageSummary,
)
from app.weather import geocode

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
PlotId = Annotated[int, Path(gt=0, le=2**63 - 1)]


def _get_plot(db: Session, plot_id: int) -> Plot:
    plot = db.query(Plot).filter(Plot.id == plot_id).first()
    if not plot:
        raise HTTPException(404, f"Plot {plot_id} not found.")
    return plot


def _check_crop_and_stage(crop_id: str, stage_id: str) -> None:
    # Same detail shape as FastAPI's own 422, so the page shows the message under the input
    if not get_crop(crop_id):
        raise HTTPException(
            422, [{"loc": ["body", "crop_id"], "msg": "Selected crop does not exist."}]
        )
    if not get_stage(crop_id, stage_id):
        raise HTTPException(
            422,
            [{"loc": ["body", "stage_id"], "msg": "Selected stage does not belong to the crop."}],
        )


def _summary(row: Assessment) -> LatestAssessment:
    return LatestAssessment(
        score=row.score,
        severity=row.severity,
        primary_hazard=row.primary_hazard,
        created_at=as_utc(row.created_at),
    )


def _latest_assessment(plot: Plot, row: Assessment | None) -> LatestAssessment | None:
    # The stored score, if it is for this plot's current location and stage
    if not matches(row, plot) or get_stage(plot.crop_id, plot.stage_id) is None:
        return None
    return _summary(row)


def _to_plot_summary(plot: Plot, row: Assessment | None) -> PlotSummary:
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
        latest_assessment=_latest_assessment(plot, row),
    )


@router.get("/plots", response_model=list[PlotSummary])
def list_plots(db: DbSession) -> list[PlotSummary]:
    # Single user with a handful of fields, so one query per plot is fine here.
    summaries = [_to_plot_summary(plot, plot.assessment) for plot in db.query(Plot)]
    # Highest risk first, unassessed last, then by name.
    summaries.sort(
        key=lambda s: (-(s.latest_assessment.score if s.latest_assessment else -1), s.name)
    )
    return summaries


@router.post("/plots", status_code=status.HTTP_201_CREATED, response_model=PlotSummary)
def create_plot(req: PlotRequest, db: DbSession) -> PlotSummary:
    _check_crop_and_stage(req.crop_id, req.stage_id)
    now = datetime.datetime.now(UTC)
    plot = Plot(**req.model_dump(), created_at=now, updated_at=now)
    db.add(plot)
    db.commit()
    db.refresh(plot)
    return _to_plot_summary(plot, None)


@router.put("/plots/{plot_id}", response_model=PlotSummary)
def update_plot(req: PlotRequest, plot_id: PlotId, db: DbSession) -> PlotSummary:
    plot = _get_plot(db, plot_id)
    _check_crop_and_stage(req.crop_id, req.stage_id)
    for field, value in req.model_dump().items():
        setattr(plot, field, value)
    plot.updated_at = datetime.datetime.now(UTC)
    db.commit()
    db.refresh(plot)
    return _to_plot_summary(plot, plot.assessment)


@router.delete("/plots/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot(plot_id: PlotId, db: DbSession) -> None:
    db.delete(_get_plot(db, plot_id))
    db.commit()


@router.get("/plots/{plot_id}/assessment", response_model=AssessmentResponse)
def get_plot_assessment(plot_id: PlotId, db: DbSession) -> AssessmentResponse:
    return AssessmentResponse(**get_assessment(_get_plot(db, plot_id), db))


@router.post("/plots/{plot_id}/assessment/refresh", response_model=AssessmentResponse)
def refresh_assessment(plot_id: PlotId, db: DbSession) -> AssessmentResponse:
    """Always fetch a new forecast and score again."""
    return AssessmentResponse(**get_assessment(_get_plot(db, plot_id), db, force=True))


@router.get("/crops", response_model=list[CropSummary])
def get_crops() -> list[CropSummary]:
    result: list[CropSummary] = []
    for crop in CROPS.values():
        sorted_stages = sorted(crop.stages.values(), key=lambda s: s.order)
        stage_summaries = [
            StageSummary(
                id=s.id,
                name=s.name,
                bbch=s.bbch,
                order=s.order,
                t_crit_heat=s.t_crit_heat,
                t_crit_frost=s.t_crit_frost,
            )
            for s in sorted_stages
        ]
        result.append(
            CropSummary(
                id=crop.id,
                common_name=crop.common_name,
                scientific_name=crop.scientific_name,
                stages=stage_summaries,
            )
        )
    return result


@router.get("/geocode", response_model=list[GeocodeCandidate])
def geocode_location(
    q: str = Query(..., min_length=2, max_length=100),
) -> list[GeocodeCandidate]:
    candidates = geocode(q)
    return [GeocodeCandidate(**c) for c in candidates]
