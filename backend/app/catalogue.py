"""The crop catalogue: threshold types, loading crops.yaml once, and lookups."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class StageConfig:
    id: str
    name: str
    bbch: str
    order: int
    t_crit_heat: float
    t_lethal_heat: float
    t_crit_frost: float
    t_lethal_frost: float
    r_crit_24h: float
    r_flood_24h: float
    w_crit_lodge: float
    w_severe: float
    weights: tuple[float, float, float, float, float]  # heat, frost, precip, disease, wind
    source: str = "unsourced"


@dataclass(frozen=True)
class CropConfig:
    id: str
    common_name: str
    scientific_name: str
    rh_crit: float
    t_min_dis: float
    t_max_dis: float
    stages: dict[str, StageConfig]
    source: str = "unsourced"


def validate_catalogue(catalogue: dict[str, CropConfig]) -> None:
    """Raise ValueError if the catalogue breaks a rule the engine relies on."""
    if not catalogue:
        raise ValueError("Catalogue has no crops")

    for crop_id, crop in catalogue.items():
        if crop.id != crop_id:
            raise ValueError(f"Crop key '{crop_id}' does not match crop.id '{crop.id}'")
        if not (0.0 <= crop.rh_crit <= 100.0):
            raise ValueError(f"Crop {crop_id}: rh_crit {crop.rh_crit} is outside 0..100")
        if crop.t_min_dis >= crop.t_max_dis:
            raise ValueError(f"Crop {crop_id}: t_min_dis must be below t_max_dis")
        if not crop.stages:
            raise ValueError(f"Crop {crop_id} has no stages")

        for stage_id, stage in crop.stages.items():
            if stage.id != stage_id:
                raise ValueError(f"Stage key '{stage_id}' does not match stage.id '{stage.id}'")
            if not stage_id.startswith(f"{crop_id}."):
                raise ValueError(f"Stage id '{stage_id}' must start with '{crop_id}.'")

            # The engine divides by these gaps, so each pair must be strictly ordered.
            if stage.t_lethal_heat <= stage.t_crit_heat:
                raise ValueError(f"Stage {stage_id}: t_lethal_heat must be above t_crit_heat")
            if stage.t_lethal_frost >= stage.t_crit_frost:
                raise ValueError(f"Stage {stage_id}: t_lethal_frost must be below t_crit_frost")
            if stage.r_flood_24h <= stage.r_crit_24h:
                raise ValueError(f"Stage {stage_id}: r_flood_24h must be above r_crit_24h")
            if stage.w_severe <= stage.w_crit_lodge:
                raise ValueError(f"Stage {stage_id}: w_severe must be above w_crit_lodge")

            if len(stage.weights) != 5 or any(w < 0.0 for w in stage.weights):
                raise ValueError(f"Stage {stage_id}: needs 5 non-negative weights")
            if abs(sum(stage.weights) - 1.0) >= 1e-9:
                raise ValueError(f"Stage {stage_id}: weights must sum to 1.0")


CROPS_FILE = Path(__file__).resolve().parent / "data" / "crops.yaml"


def parse_catalogue(text: str) -> dict[str, CropConfig]:
    data = yaml.safe_load(text)
    if not isinstance(data, dict) or not isinstance(data.get("crops"), dict):
        raise ValueError("crops.yaml needs a top-level 'crops' mapping")

    crops: dict[str, CropConfig] = {}
    for crop_id, raw in data["crops"].items():
        stages = {
            str(stage_id): StageConfig(
                id=str(s["id"]),
                name=str(s["name"]),
                bbch=str(s["bbch"]),
                order=int(s["order"]),
                t_crit_heat=float(s["t_crit_heat"]),
                t_lethal_heat=float(s["t_lethal_heat"]),
                t_crit_frost=float(s["t_crit_frost"]),
                t_lethal_frost=float(s["t_lethal_frost"]),
                r_crit_24h=float(s["r_crit_24h"]),
                r_flood_24h=float(s["r_flood_24h"]),
                w_crit_lodge=float(s["w_crit_lodge"]),
                w_severe=float(s["w_severe"]),
                weights=tuple(float(w) for w in s["weights"]),
                source=str(s.get("source", "unsourced")),
            )
            for stage_id, s in raw.get("stages", {}).items()
        }
        crops[str(crop_id)] = CropConfig(
            id=str(raw["id"]),
            common_name=str(raw["common_name"]),
            scientific_name=str(raw["scientific_name"]),
            rh_crit=float(raw["rh_crit"]),
            t_min_dis=float(raw["t_min_dis"]),
            t_max_dis=float(raw["t_max_dis"]),
            stages=stages,
            source=str(raw.get("source", "unsourced")),
        )

    validate_catalogue(crops)
    return crops


CROPS: dict[str, CropConfig] = parse_catalogue(CROPS_FILE.read_text(encoding="utf-8"))


def get_crop(crop_id: str) -> CropConfig | None:
    return CROPS.get(crop_id)


def get_stage(crop_id: str, stage_id: str) -> StageConfig | None:
    crop = CROPS.get(crop_id)
    return crop.stages.get(stage_id) if crop else None
