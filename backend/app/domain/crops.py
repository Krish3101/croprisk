"""Pure domain models and catalogue for crops and growth stages."""

from dataclasses import dataclass


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


@dataclass(frozen=True)
class CropConfig:
    id: str
    common_name: str
    scientific_name: str
    rh_crit: float
    t_min_dis: float
    t_max_dis: float
    stages: dict[str, StageConfig]


CROPS: dict[str, CropConfig] = {
    "wheat": CropConfig(
        id="wheat",
        common_name="Wheat",
        scientific_name="Triticum aestivum",
        rh_crit=80.0,
        t_min_dis=15.0,
        t_max_dis=25.0,
        stages={
            "wheat.emergence": StageConfig(
                id="wheat.emergence",
                name="Emergence / Seedling",
                bbch="00–19",
                order=1,
                t_crit_heat=32.0,
                t_lethal_heat=38.0,
                t_crit_frost=-2.0,
                t_lethal_frost=-6.0,
                r_crit_24h=45.0,
                r_flood_24h=90.0,
                w_crit_lodge=50.0,
                w_severe=80.0,
                weights=(0.15, 0.25, 0.35, 0.20, 0.05),
            ),
            "wheat.tillering": StageConfig(
                id="wheat.tillering",
                name="Tillering / Jointing",
                bbch="20–39",
                order=2,
                t_crit_heat=30.0,
                t_lethal_heat=36.0,
                t_crit_frost=-3.0,
                t_lethal_frost=-8.0,
                r_crit_24h=50.0,
                r_flood_24h=100.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.10, 0.20, 0.30, 0.30, 0.10),
            ),
            "wheat.anthesis": StageConfig(
                id="wheat.anthesis",
                name="Flowering / Anthesis",
                bbch="61–69",
                order=3,
                t_crit_heat=27.0,
                t_lethal_heat=34.0,
                t_crit_frost=1.0,
                t_lethal_frost=-2.0,
                r_crit_24h=35.0,
                r_flood_24h=75.0,
                w_crit_lodge=40.0,
                w_severe=65.0,
                weights=(0.35, 0.30, 0.15, 0.15, 0.05),
            ),
            "wheat.grain_fill": StageConfig(
                id="wheat.grain_fill",
                name="Grain Filling",
                bbch="71–85",
                order=4,
                t_crit_heat=28.0,
                t_lethal_heat=35.0,
                t_crit_frost=0.0,
                t_lethal_frost=-3.0,
                r_crit_24h=40.0,
                r_flood_24h=80.0,
                w_crit_lodge=35.0,
                w_severe=55.0,
                weights=(0.30, 0.10, 0.20, 0.15, 0.25),
            ),
            "wheat.ripening": StageConfig(
                id="wheat.ripening",
                name="Ripening / Harvest",
                bbch="87–92",
                order=5,
                t_crit_heat=35.0,
                t_lethal_heat=42.0,
                t_crit_frost=0.0,
                t_lethal_frost=-4.0,
                r_crit_24h=25.0,
                r_flood_24h=50.0,
                w_crit_lodge=30.0,
                w_severe=50.0,
                weights=(0.10, 0.05, 0.35, 0.15, 0.35),
            ),
        },
    ),
    "rice": CropConfig(
        id="rice",
        common_name="Rice / Paddy",
        scientific_name="Oryza sativa",
        rh_crit=85.0,
        t_min_dis=22.0,
        t_max_dis=32.0,
        stages={
            "rice.seedling": StageConfig(
                id="rice.seedling",
                name="Seedling / Nursery",
                bbch="00–19",
                order=1,
                t_crit_heat=36.0,
                t_lethal_heat=42.0,
                t_crit_frost=12.0,
                t_lethal_frost=5.0,
                r_crit_24h=80.0,
                r_flood_24h=160.0,
                w_crit_lodge=50.0,
                w_severe=80.0,
                weights=(0.20, 0.35, 0.20, 0.20, 0.05),
            ),
            "rice.tillering": StageConfig(
                id="rice.tillering",
                name="Tillering / Vegetative",
                bbch="20–39",
                order=2,
                t_crit_heat=37.0,
                t_lethal_heat=43.0,
                t_crit_frost=10.0,
                t_lethal_frost=4.0,
                r_crit_24h=120.0,
                r_flood_24h=220.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.15, 0.20, 0.15, 0.35, 0.15),
            ),
            "rice.panicle": StageConfig(
                id="rice.panicle",
                name="Panicle Initiation / Anthesis",
                bbch="51–69",
                order=3,
                t_crit_heat=34.0,
                t_lethal_heat=39.0,
                t_crit_frost=15.0,
                t_lethal_frost=8.0,
                r_crit_24h=70.0,
                r_flood_24h=140.0,
                w_crit_lodge=40.0,
                w_severe=65.0,
                weights=(0.40, 0.25, 0.10, 0.15, 0.10),
            ),
            "rice.milk": StageConfig(
                id="rice.milk",
                name="Milk / Dough",
                bbch="71–85",
                order=4,
                t_crit_heat=35.0,
                t_lethal_heat=40.0,
                t_crit_frost=12.0,
                t_lethal_frost=6.0,
                r_crit_24h=80.0,
                r_flood_24h=150.0,
                w_crit_lodge=35.0,
                w_severe=60.0,
                weights=(0.25, 0.15, 0.20, 0.15, 0.25),
            ),
            "rice.maturity": StageConfig(
                id="rice.maturity",
                name="Maturity / Harvest",
                bbch="87–92",
                order=5,
                t_crit_heat=38.0,
                t_lethal_heat=44.0,
                t_crit_frost=10.0,
                t_lethal_frost=4.0,
                r_crit_24h=40.0,
                r_flood_24h=80.0,
                w_crit_lodge=30.0,
                w_severe=50.0,
                weights=(0.05, 0.05, 0.40, 0.15, 0.35),
            ),
        },
    ),
    "cotton": CropConfig(
        id="cotton",
        common_name="Cotton",
        scientific_name="Gossypium hirsutum",
        rh_crit=80.0,
        t_min_dis=20.0,
        t_max_dis=30.0,
        stages={
            "cotton.emergence": StageConfig(
                id="cotton.emergence",
                name="Emergence / Seedling",
                bbch="00–19",
                order=1,
                t_crit_heat=38.0,
                t_lethal_heat=45.0,
                t_crit_frost=8.0,
                t_lethal_frost=2.0,
                r_crit_24h=40.0,
                r_flood_24h=80.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.15, 0.30, 0.35, 0.15, 0.05),
            ),
            "cotton.squaring": StageConfig(
                id="cotton.squaring",
                name="Squaring (Budding)",
                bbch="51–59",
                order=2,
                t_crit_heat=38.0,
                t_lethal_heat=44.0,
                t_crit_frost=6.0,
                t_lethal_frost=1.0,
                r_crit_24h=50.0,
                r_flood_24h=100.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.25, 0.15, 0.25, 0.25, 0.10),
            ),
            "cotton.flowering": StageConfig(
                id="cotton.flowering",
                name="Peak Flowering",
                bbch="60–69",
                order=3,
                t_crit_heat=36.0,
                t_lethal_heat=42.0,
                t_crit_frost=8.0,
                t_lethal_frost=2.0,
                r_crit_24h=45.0,
                r_flood_24h=90.0,
                w_crit_lodge=40.0,
                w_severe=65.0,
                weights=(0.40, 0.15, 0.20, 0.15, 0.10),
            ),
            "cotton.boll_open": StageConfig(
                id="cotton.boll_open",
                name="Boll Opening",
                bbch="71–85",
                order=4,
                t_crit_heat=39.0,
                t_lethal_heat=46.0,
                t_crit_frost=5.0,
                t_lethal_frost=0.0,
                r_crit_24h=30.0,
                r_flood_24h=60.0,
                w_crit_lodge=35.0,
                w_severe=60.0,
                weights=(0.15, 0.10, 0.35, 0.25, 0.15),
            ),
            "cotton.harvest": StageConfig(
                id="cotton.harvest",
                name="Harvest / Picking",
                bbch="87–92",
                order=5,
                t_crit_heat=40.0,
                t_lethal_heat=48.0,
                t_crit_frost=4.0,
                t_lethal_frost=0.0,
                r_crit_24h=20.0,
                r_flood_24h=40.0,
                w_crit_lodge=30.0,
                w_severe=50.0,
                weights=(0.05, 0.05, 0.50, 0.15, 0.25),
            ),
        },
    ),
    "soybean": CropConfig(
        id="soybean",
        common_name="Soybean",
        scientific_name="Glycine max",
        rh_crit=82.0,
        t_min_dis=20.0,
        t_max_dis=28.0,
        stages={
            "soybean.emergence": StageConfig(
                id="soybean.emergence",
                name="Emergence / Unifoliate",
                bbch="00–19",
                order=1,
                t_crit_heat=35.0,
                t_lethal_heat=42.0,
                t_crit_frost=4.0,
                t_lethal_frost=-1.0,
                r_crit_24h=45.0,
                r_flood_24h=90.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.15, 0.30, 0.35, 0.15, 0.05),
            ),
            "soybean.vegetative": StageConfig(
                id="soybean.vegetative",
                name="Vegetative Canopy",
                bbch="20–49",
                order=2,
                t_crit_heat=36.0,
                t_lethal_heat=43.0,
                t_crit_frost=2.0,
                t_lethal_frost=-2.0,
                r_crit_24h=55.0,
                r_flood_24h=110.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.15, 0.15, 0.25, 0.35, 0.10),
            ),
            "soybean.flowering": StageConfig(
                id="soybean.flowering",
                name="Flowering / Anthesis",
                bbch="60–69",
                order=3,
                t_crit_heat=32.0,
                t_lethal_heat=38.0,
                t_crit_frost=5.0,
                t_lethal_frost=0.0,
                r_crit_24h=45.0,
                r_flood_24h=90.0,
                w_crit_lodge=40.0,
                w_severe=65.0,
                weights=(0.35, 0.20, 0.20, 0.20, 0.05),
            ),
            "soybean.pod_dev": StageConfig(
                id="soybean.pod_dev",
                name="Pod Development",
                bbch="71–79",
                order=4,
                t_crit_heat=34.0,
                t_lethal_heat=40.0,
                t_crit_frost=3.0,
                t_lethal_frost=-1.0,
                r_crit_24h=45.0,
                r_flood_24h=90.0,
                w_crit_lodge=35.0,
                w_severe=60.0,
                weights=(0.25, 0.15, 0.25, 0.20, 0.15),
            ),
            "soybean.maturity": StageConfig(
                id="soybean.maturity",
                name="Maturity / Harvest",
                bbch="89–92",
                order=5,
                t_crit_heat=37.0,
                t_lethal_heat=44.0,
                t_crit_frost=2.0,
                t_lethal_frost=-2.0,
                r_crit_24h=25.0,
                r_flood_24h=50.0,
                w_crit_lodge=30.0,
                w_severe=50.0,
                weights=(0.05, 0.05, 0.45, 0.15, 0.30),
            ),
        },
    ),
    "maize": CropConfig(
        id="maize",
        common_name="Maize",
        scientific_name="Zea mays",
        rh_crit=85.0,
        t_min_dis=18.0,
        t_max_dis=28.0,
        stages={
            "maize.emergence": StageConfig(
                id="maize.emergence",
                name="Seedling / Emergence",
                bbch="00–19",
                order=1,
                t_crit_heat=36.0,
                t_lethal_heat=43.0,
                t_crit_frost=4.0,
                t_lethal_frost=-1.0,
                r_crit_24h=50.0,
                r_flood_24h=100.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.15, 0.30, 0.35, 0.15, 0.05),
            ),
            "maize.whorl": StageConfig(
                id="maize.whorl",
                name="Whorl / Knee High",
                bbch="20–39",
                order=2,
                t_crit_heat=37.0,
                t_lethal_heat=44.0,
                t_crit_frost=2.0,
                t_lethal_frost=-2.0,
                r_crit_24h=65.0,
                r_flood_24h=130.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.15, 0.15, 0.30, 0.25, 0.15),
            ),
            "maize.silking": StageConfig(
                id="maize.silking",
                name="Tasseling / Silking",
                bbch="61–69",
                order=3,
                t_crit_heat=34.0,
                t_lethal_heat=39.0,
                t_crit_frost=5.0,
                t_lethal_frost=0.0,
                r_crit_24h=50.0,
                r_flood_24h=100.0,
                w_crit_lodge=35.0,
                w_severe=60.0,
                weights=(0.40, 0.20, 0.15, 0.10, 0.15),
            ),
            "maize.grain_fill": StageConfig(
                id="maize.grain_fill",
                name="Grain Fill (Milk/Dent)",
                bbch="71–85",
                order=4,
                t_crit_heat=35.0,
                t_lethal_heat=41.0,
                t_crit_frost=3.0,
                t_lethal_frost=-2.0,
                r_crit_24h=55.0,
                r_flood_24h=110.0,
                w_crit_lodge=35.0,
                w_severe=55.0,
                weights=(0.25, 0.10, 0.20, 0.15, 0.30),
            ),
            "maize.maturity": StageConfig(
                id="maize.maturity",
                name="Maturity / Harvest",
                bbch="87–92",
                order=5,
                t_crit_heat=38.0,
                t_lethal_heat=45.0,
                t_crit_frost=1.0,
                t_lethal_frost=-3.0,
                r_crit_24h=30.0,
                r_flood_24h=60.0,
                w_crit_lodge=30.0,
                w_severe=50.0,
                weights=(0.05, 0.05, 0.40, 0.15, 0.35),
            ),
        },
    ),
    "mustard": CropConfig(
        id="mustard",
        common_name="Mustard",
        scientific_name="Brassica juncea",
        rh_crit=80.0,
        t_min_dis=12.0,
        t_max_dis=22.0,
        stages={
            "mustard.emergence": StageConfig(
                id="mustard.emergence",
                name="Seedling / Emergence",
                bbch="00–19",
                order=1,
                t_crit_heat=32.0,
                t_lethal_heat=38.0,
                t_crit_frost=1.0,
                t_lethal_frost=-4.0,
                r_crit_24h=40.0,
                r_flood_24h=80.0,
                w_crit_lodge=45.0,
                w_severe=75.0,
                weights=(0.15, 0.30, 0.35, 0.15, 0.05),
            ),
            "mustard.rosette": StageConfig(
                id="mustard.rosette",
                name="Rosette / Branching",
                bbch="20–39",
                order=2,
                t_crit_heat=30.0,
                t_lethal_heat=36.0,
                t_crit_frost=0.0,
                t_lethal_frost=-5.0,
                r_crit_24h=45.0,
                r_flood_24h=90.0,
                w_crit_lodge=40.0,
                w_severe=70.0,
                weights=(0.10, 0.25, 0.25, 0.30, 0.10),
            ),
            "mustard.flowering": StageConfig(
                id="mustard.flowering",
                name="Flowering / Anthesis",
                bbch="60–69",
                order=3,
                t_crit_heat=27.0,
                t_lethal_heat=33.0,
                t_crit_frost=2.0,
                t_lethal_frost=-2.0,
                r_crit_24h=30.0,
                r_flood_24h=60.0,
                w_crit_lodge=35.0,
                w_severe=60.0,
                weights=(0.30, 0.35, 0.15, 0.15, 0.05),
            ),
            "mustard.siliqua": StageConfig(
                id="mustard.siliqua",
                name="Pod Formation (Siliqua)",
                bbch="71–85",
                order=4,
                t_crit_heat=28.0,
                t_lethal_heat=34.0,
                t_crit_frost=1.0,
                t_lethal_frost=-3.0,
                r_crit_24h=35.0,
                r_flood_24h=70.0,
                w_crit_lodge=30.0,
                w_severe=55.0,
                weights=(0.30, 0.15, 0.20, 0.15, 0.20),
            ),
            "mustard.maturity": StageConfig(
                id="mustard.maturity",
                name="Maturity / Harvest",
                bbch="89–92",
                order=5,
                t_crit_heat=34.0,
                t_lethal_heat=40.0,
                t_crit_frost=0.0,
                t_lethal_frost=-4.0,
                r_crit_24h=20.0,
                r_flood_24h=45.0,
                w_crit_lodge=25.0,
                w_severe=45.0,
                weights=(0.05, 0.05, 0.40, 0.15, 0.35),
            ),
        },
    ),
}


def get_crop(crop_id: str) -> CropConfig | None:
    return CROPS.get(crop_id)


def get_stage(crop_id: str, stage_id: str) -> StageConfig | None:
    crop = CROPS.get(crop_id)
    if not crop:
        return None
    return crop.stages.get(stage_id)


def validate_catalogue() -> None:
    """Startup and test assertion for catalogue integrity.

    Enforces:
    - exactly 5 stages per crop with order 1-5;
    - t_lethal_heat > t_crit_heat;
    - t_lethal_frost < t_crit_frost;
    - r_flood_24h > r_crit_24h;
    - w_severe > w_crit_lodge;
    - weights non-negative and summing to 1.0 within 1e-9.
    """
    assert len(CROPS) == 6, f"Expected 6 crops, found {len(CROPS)}"

    for crop_id, crop in CROPS.items():
        assert len(crop.stages) == 5, f"Crop {crop_id} has {len(crop.stages)} stages, expected 5"
        orders = sorted(s.order for s in crop.stages.values())
        assert orders == [1, 2, 3, 4, 5], f"Crop {crop_id} orders must be 1..5, found {orders}"

        for stage_id, stage in crop.stages.items():
            prefix = f"Stage {stage_id}:"
            assert stage.t_lethal_heat > stage.t_crit_heat, (
                f"{prefix} t_lethal_heat ({stage.t_lethal_heat}) <= t_crit_heat ({stage.t_crit_heat})"
            )
            assert stage.t_lethal_frost < stage.t_crit_frost, (
                f"{prefix} t_lethal_frost ({stage.t_lethal_frost}) >= t_crit_frost ({stage.t_crit_frost})"
            )
            assert stage.r_flood_24h > stage.r_crit_24h, (
                f"{prefix} r_flood_24h ({stage.r_flood_24h}) <= r_crit_24h ({stage.r_crit_24h})"
            )
            assert stage.w_severe > stage.w_crit_lodge, (
                f"{prefix} w_severe ({stage.w_severe}) <= w_crit_lodge ({stage.w_crit_lodge})"
            )

            assert len(stage.weights) == 5, f"{prefix} must have 5 weights"
            for w in stage.weights:
                assert w >= 0.0, f"{prefix} negative weight {w}"
            weight_sum = sum(stage.weights)
            assert abs(weight_sum - 1.0) < 1e-9, (
                f"{prefix} weights sum to {weight_sum}, expected 1.0 within 1e-9"
            )
