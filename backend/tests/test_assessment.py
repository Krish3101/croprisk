import datetime
from datetime import UTC, timedelta
from unittest.mock import Mock

import pytest
from conftest import make_intervals
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.errors import CatalogueMismatchError, UpstreamUnavailableError
from app.models import Plot, RiskAssessment
from app.services import assessment
from app.services.assessment import get_plot_risk

T0 = datetime.datetime(2026, 9, 10, 6, 0, tzinfo=UTC)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    session.add(
        Plot(
            name="Field A",
            crop_id="wheat",
            stage_id="wheat.anthesis",
            location_name="Pune, India",
            latitude=18.5,
            longitude=73.8,
            sowing_date=datetime.date(2026, 1, 1),
            created_at=T0.isoformat(),
            updated_at=T0.isoformat(),
        )
    )
    session.commit()
    yield session
    session.close()


def plot_of(db) -> Plot:
    return db.query(Plot).one()


def down() -> Mock:
    return Mock(side_effect=UpstreamUnavailableError("Provider down"))


def test_first_call_fetches_then_cache_hits(db):
    weather = Mock(return_value=make_intervals(temp=20.0))
    first = get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)
    second = get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0 + timedelta(hours=11))

    assert weather.call_count == 1
    assert first["refreshed"] is True
    assert second["refreshed"] is False
    assert second["risk"]["is_stale"] is False
    assert second["risk"]["forecast_fetched_at"] == T0.isoformat()


def test_stage_change_rescores_without_network_call(db):
    weather = Mock(return_value=make_intervals(temp=38.0))
    assert get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)["risk"]["score"] == 100

    plot_of(db).stage_id = "wheat.ripening"
    db.commit()
    res = get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0 + timedelta(hours=1))

    assert weather.call_count == 1
    assert res["risk"]["score"] == 17
    assert res["plot"]["stage_id"] == "wheat.ripening"


def test_catalogue_change_rescores_without_network_call(db, monkeypatch):
    weather = Mock(return_value=make_intervals(temp=38.0))
    get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)

    monkeypatch.setattr(assessment, "CATALOGUE_VERSION", "edited-yaml")
    get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0 + timedelta(hours=1))

    assert weather.call_count == 1
    assert db.query(RiskAssessment).one().catalogue_version == "edited-yaml"


def test_location_change_fetches_again(db):
    weather = Mock(return_value=make_intervals(temp=20.0))
    get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)

    plot_of(db).latitude = 30.9
    db.commit()
    res = get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0 + timedelta(hours=1))

    assert weather.call_count == 2
    assert res["refreshed"] is True
    assert db.query(RiskAssessment).one().location_key == "30.90:73.80"


def test_location_change_never_serves_old_place_when_provider_down(db):
    get_plot_risk(plot_of(db), db, weather_provider=Mock(return_value=make_intervals()), now=T0)
    plot_of(db).longitude = 75.8
    db.commit()

    with pytest.raises(UpstreamUnavailableError):
        get_plot_risk(plot_of(db), db, weather_provider=down(), now=T0 + timedelta(hours=1))


def test_forced_refresh_respects_cooldown(db):
    weather = Mock(return_value=make_intervals(temp=20.0))
    get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)

    inside = get_plot_risk(
        plot_of(db), db, force=True, weather_provider=weather, now=T0 + timedelta(minutes=2)
    )
    assert weather.call_count == 1
    assert inside["refreshed"] is False

    after = get_plot_risk(
        plot_of(db), db, force=True, weather_provider=weather, now=T0 + timedelta(minutes=11)
    )
    assert weather.call_count == 2
    assert after["refreshed"] is True


def test_forecast_older_than_ttl_is_fetched_again(db):
    weather = Mock(return_value=make_intervals(temp=20.0))
    get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)
    get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0 + timedelta(hours=13))
    assert weather.call_count == 2


def test_stale_serve_is_capped_at_48_hours(db):
    get_plot_risk(plot_of(db), db, weather_provider=Mock(return_value=make_intervals()), now=T0)

    res = get_plot_risk(plot_of(db), db, weather_provider=down(), now=T0 + timedelta(hours=24))
    assert res["risk"]["is_stale"] is True

    with pytest.raises(UpstreamUnavailableError):
        get_plot_risk(plot_of(db), db, weather_provider=down(), now=T0 + timedelta(hours=49))


def test_stage_flips_do_not_reset_the_forecast_clock(db):
    weather = Mock(return_value=make_intervals(temp=20.0))
    get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)
    stages = ["wheat.ripening", "wheat.anthesis"]

    # Re-scores at +11 h are free, but by +22 h the forecast is past the 12 h TTL.
    plot_of(db).stage_id = stages[0]
    db.commit()
    res = get_plot_risk(plot_of(db), db, weather_provider=down(), now=T0 + timedelta(hours=11))
    assert res["risk"]["is_stale"] is False

    for i, hours in enumerate([22, 33, 44]):
        plot_of(db).stage_id = stages[(i + 1) % 2]
        db.commit()
        res = get_plot_risk(
            plot_of(db), db, weather_provider=down(), now=T0 + timedelta(hours=hours)
        )
        assert res["risk"]["is_stale"] is True
        assert res["plot"]["stage_id"] == plot_of(db).stage_id

    plot_of(db).stage_id = "wheat.ripening"
    db.commit()
    with pytest.raises(UpstreamUnavailableError):
        get_plot_risk(plot_of(db), db, weather_provider=down(), now=T0 + timedelta(hours=55))
    assert db.query(RiskAssessment).one().forecast_fetched_at == T0.isoformat()


def test_bug_in_scoring_is_not_hidden_by_stale_serve(db):
    get_plot_risk(plot_of(db), db, weather_provider=Mock(return_value=make_intervals()), now=T0)
    broken = Mock(side_effect=KeyError("bug"))

    with pytest.raises(KeyError):
        get_plot_risk(
            plot_of(db), db, force=True, weather_provider=broken, now=T0 + timedelta(hours=1)
        )


def test_stage_missing_from_catalogue_is_a_conflict(db):
    plot_of(db).stage_id = "wheat.removed"
    db.commit()
    weather = Mock(return_value=make_intervals())

    with pytest.raises(CatalogueMismatchError):
        get_plot_risk(plot_of(db), db, weather_provider=weather, now=T0)
    assert weather.call_count == 0
