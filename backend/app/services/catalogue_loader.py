"""Reads crops.yaml once at import, validates it and fingerprints it."""

import hashlib
from pathlib import Path

import yaml

from app.domain.catalogue import CropConfig, StageConfig, validate_catalogue

CROPS_FILE = Path(__file__).resolve().parent.parent / "data" / "crops.yaml"


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


_raw = CROPS_FILE.read_bytes()
CROPS: dict[str, CropConfig] = parse_catalogue(_raw.decode("utf-8"))
# Stored on each assessment row so editing the YAML forces a re-score.
CATALOGUE_VERSION: str = hashlib.sha256(_raw).hexdigest()[:12]


def get_crop(crop_id: str) -> CropConfig | None:
    return CROPS.get(crop_id)


def get_stage(crop_id: str, stage_id: str) -> StageConfig | None:
    crop = CROPS.get(crop_id)
    return crop.stages.get(stage_id) if crop else None
