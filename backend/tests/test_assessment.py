import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.domain.engine import ForecastInterval
from app.errors import UpstreamUnavailableError
from app.models import Plot, RiskAssessment, User
from app.services.assessment import get_plot_risk


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = User(
        email="grower@example.com",
        password_hash="hash",
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    now_iso = datetime.datetime.now(datetime.UTC).isoformat()
    plot = Plot(
        user_id=user.id,
        name="Field A",
        crop_id="wheat",
        stage_id="wheat.anthesis",
        location_name="Pune, India",
        latitude=18.5,
        longitude=73.8,
        sowing_date=datetime.date(2026, 1, 1),
        created_at=now_iso,
        updated_at=now_iso,
    )
    session.add(plot)
    session.commit()
    session.refresh(plot)

    yield session
    session.close()


def make_intervals(temp: float = 20.0):
    return [
        ForecastInterval(
            timestamp=f"2026-09-10T{i*3:02d}:00:00Z",
            temperature_c=temp,
            relative_humidity=50.0,
            wind_kmh=10.0,
            rain_mm=0.0,
        )
        for i in range(40)
    ]


def test_assessment_initial_compute_and_cache_hit(db_session):
    plot = db_session.query(Plot).first()

    mock_weather = Mock(return_value=make_intervals(20.0))
    # 1. Initial compute
    res1 = get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)
    assert mock_weather.call_count == 1
    assert res1["risk"]["is_stale"] is False
    assert res1["risk"]["score"] == 0

    # 2. Subsequent call within 12 hours: cache hit, zero weather calls
    mock_weather.reset_mock()
    res2 = get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)
    assert mock_weather.call_count == 0
    assert res2["risk"]["is_stale"] is False
    assert res2["risk"]["score"] == 0


def test_assessment_forced_refresh_calls_weather(db_session):
    plot = db_session.query(Plot).first()

    mock_weather = Mock(return_value=make_intervals(20.0))
    get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)
    assert mock_weather.call_count == 1

    # Call with refresh=True
    get_plot_risk(plot, db_session, refresh=True, weather_provider=mock_weather)
    assert mock_weather.call_count == 2


def test_assessment_expired_cache_recomputes(db_session):
    plot = db_session.query(Plot).first()

    mock_weather = Mock(return_value=make_intervals(20.0))
    get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)
    assert mock_weather.call_count == 1

    # Backdate stored assessment by 13 hours
    row = db_session.query(RiskAssessment).filter_by(plot_id=plot.id).first()
    old_time = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=13)).isoformat()
    row.created_at = old_time
    db_session.commit()

    # Next call should fetch weather again
    mock_weather.reset_mock()
    get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)
    assert mock_weather.call_count == 1


def test_plot_update_invalidates_cache(db_session):
    plot = db_session.query(Plot).first()

    mock_weather = Mock(return_value=make_intervals(20.0))
    get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)
    assert mock_weather.call_count == 1

    # Edit plot growth stage -> bumps updated_at to future of assessment created_at
    future_time = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=2)).isoformat()
    plot.updated_at = future_time
    plot.stage_id = "wheat.ripening"
    db_session.commit()

    # Stored row created_at is now older than plot.updated_at -> must recompute
    mock_weather.reset_mock()
    get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)
    assert mock_weather.call_count == 1


def test_provider_down_with_valid_stored_row_serves_stale(db_session):
    plot = db_session.query(Plot).first()

    # Initial assessment succeeds
    mock_weather = Mock(return_value=make_intervals(20.0))
    get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)

    # Provider is now down
    failing_weather = Mock(side_effect=UpstreamUnavailableError("Provider offline"))
    # Call with refresh=True to bypass 12h freshness check and force weather call
    res = get_plot_risk(plot, db_session, refresh=True, weather_provider=failing_weather)
    assert res["risk"]["is_stale"] is True


def test_provider_down_without_stored_row_raises_503(db_session):
    plot = db_session.query(Plot).first()
    failing_weather = Mock(side_effect=UpstreamUnavailableError("Provider offline"))

    with pytest.raises(UpstreamUnavailableError):
        get_plot_risk(plot, db_session, refresh=False, weather_provider=failing_weather)


def test_provider_down_after_stage_change_raises_503(db_session):
    plot = db_session.query(Plot).first()

    # Initial assessment for wheat.anthesis
    mock_weather = Mock(return_value=make_intervals(20.0))
    get_plot_risk(plot, db_session, refresh=False, weather_provider=mock_weather)

    # Stage changed to wheat.ripening
    plot.updated_at = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=5)).isoformat()
    plot.stage_id = "wheat.ripening"
    db_session.commit()

    # Weather provider fails -> old assessment answers different question, must NOT be served even degraded!
    failing_weather = Mock(side_effect=UpstreamUnavailableError("Provider offline"))
    with pytest.raises(UpstreamUnavailableError):
        get_plot_risk(plot, db_session, refresh=False, weather_provider=failing_weather)
