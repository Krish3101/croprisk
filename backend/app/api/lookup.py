"""Lookup routes: crops catalogue and geocoding."""

from fastapi import APIRouter, Query

from app.schemas import CropSummary, GeocodeCandidate, StageSummary
from app.services.catalogue_loader import CROPS
from app.services.weather import geocode

router = APIRouter(tags=["lookup"])


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
