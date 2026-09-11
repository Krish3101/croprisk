from app.domain.crops import CROPS, get_crop, get_stage, validate_catalogue


def test_catalogue_integrity():
    validate_catalogue()


def test_catalogue_structure():
    assert len(CROPS) == 6
    assert set(CROPS.keys()) == {"wheat", "rice", "cotton", "soybean", "maize", "mustard"}

    for crop_id, crop in CROPS.items():
        assert crop.id == crop_id
        assert crop.common_name
        assert crop.scientific_name
        assert len(crop.stages) == 5
        orders = [s.order for s in crop.stages.values()]
        assert sorted(orders) == [1, 2, 3, 4, 5]


def test_get_crop_and_stage():
    wheat = get_crop("wheat")
    assert wheat is not None
    assert wheat.common_name == "Wheat"

    unknown = get_crop("unknown_crop")
    assert unknown is None

    stage = get_stage("wheat", "wheat.anthesis")
    assert stage is not None
    assert stage.name == "Flowering / Anthesis"

    bad_stage = get_stage("wheat", "wheat.invalid")
    assert bad_stage is None

    bad_crop_stage = get_stage("invalid", "anything")
    assert bad_crop_stage is None
