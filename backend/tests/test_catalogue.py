import dataclasses

import pytest

from app.domain.catalogue import CropConfig, StageConfig, validate_catalogue
from app.services.catalogue_loader import (
    CATALOGUE_VERSION,
    CROPS,
    get_crop,
    get_stage,
    parse_catalogue,
)

GOOD_STAGE = StageConfig(
    id="test.one",
    name="Stage one",
    bbch="00",
    order=1,
    t_crit_heat=30.0,
    t_lethal_heat=36.0,
    t_crit_frost=0.0,
    t_lethal_frost=-4.0,
    r_crit_24h=50.0,
    r_flood_24h=100.0,
    w_crit_lodge=40.0,
    w_severe=70.0,
    weights=(0.2, 0.2, 0.2, 0.2, 0.2),
)
GOOD_CROP = CropConfig(
    id="test",
    common_name="Test",
    scientific_name="Testus",
    rh_crit=80.0,
    t_min_dis=15.0,
    t_max_dis=25.0,
    stages={"test.one": GOOD_STAGE},
)


def with_stage(**changes) -> dict[str, CropConfig]:
    stage = dataclasses.replace(GOOD_STAGE, **changes)
    return {"test": dataclasses.replace(GOOD_CROP, stages={stage.id: stage})}


def test_shipped_catalogue_loads_and_is_unsourced():
    validate_catalogue(CROPS)
    assert len(CATALOGUE_VERSION) == 12
    assert set(CROPS) == {"wheat", "rice", "cotton", "soybean", "maize", "mustard"}
    for crop in CROPS.values():
        assert crop.source == "unsourced"
        assert all(stage.source == "unsourced" for stage in crop.stages.values())


def test_get_crop_and_stage():
    assert get_crop("wheat").common_name == "Wheat"
    assert get_stage("wheat", "wheat.anthesis").name == "Flowering / Anthesis"
    assert get_crop("unknown") is None
    assert get_stage("wheat", "wheat.invalid") is None
    assert get_stage("invalid", "anything") is None


def test_valid_minimal_catalogue_passes():
    validate_catalogue({"test": GOOD_CROP})


def test_empty_catalogue_rejected():
    with pytest.raises(ValueError, match="no crops"):
        validate_catalogue({})


def test_crop_key_must_match_id():
    with pytest.raises(ValueError, match="does not match crop.id"):
        validate_catalogue({"other": GOOD_CROP})


def test_stage_key_must_match_id():
    crop = dataclasses.replace(GOOD_CROP, stages={"test.two": GOOD_STAGE})
    with pytest.raises(ValueError, match="does not match stage.id"):
        validate_catalogue({"test": crop})


def test_stage_id_needs_crop_prefix():
    with pytest.raises(ValueError, match="must start with 'test.'"):
        validate_catalogue(with_stage(id="wheat.one"))


def test_disease_band_must_be_ordered():
    crop = dataclasses.replace(GOOD_CROP, t_min_dis=25.0, t_max_dis=25.0)
    with pytest.raises(ValueError, match="t_min_dis"):
        validate_catalogue({"test": crop})


@pytest.mark.parametrize("rh", [-1.0, 100.5])
def test_rh_crit_must_be_a_percentage(rh):
    crop = dataclasses.replace(GOOD_CROP, rh_crit=rh)
    with pytest.raises(ValueError, match="rh_crit"):
        validate_catalogue({"test": crop})


def test_lethal_heat_must_be_above_critical():
    with pytest.raises(ValueError, match="t_lethal_heat"):
        validate_catalogue(with_stage(t_lethal_heat=30.0))


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1.0"):
        validate_catalogue(with_stage(weights=(0.5, 0.5, 0.5, 0.0, 0.0)))


def test_yaml_without_crops_mapping_rejected():
    with pytest.raises(ValueError, match="'crops' mapping"):
        parse_catalogue("plants: []\n")
