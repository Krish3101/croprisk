import datetime
import os
import tempfile
from datetime import UTC, timedelta
from pathlib import Path

# Environment variables win over backend/.env, so blank the keys and point the app
# at a throwaway database before anything imports app.config.
os.environ["OPENWEATHER_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
TEST_DB = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from app.domain.engine import ForecastInterval  # noqa: E402


def make_intervals(
    count: int = 40,
    start: datetime.datetime | None = None,
    step_hours: int = 3,
    temp: float = 25.0,
    rh: float = 60.0,
    wind: float = 10.0,
    rain: float = 0.0,
) -> list[ForecastInterval]:
    """Valid forecast intervals on a 3-hour cadence."""
    if start is None:
        start = datetime.datetime(2026, 9, 10, 0, 0, 0, tzinfo=UTC)
    return [
        ForecastInterval(
            timestamp=(start + timedelta(hours=i * step_hours)).isoformat(),
            temperature_c=temp,
            relative_humidity=rh,
            wind_kmh=wind,
            rain_mm=rain,
        )
        for i in range(count)
    ]
