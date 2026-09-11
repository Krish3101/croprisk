# CropRisk

Turns a five-day weather forecast into a risk score for a specific crop at its current
growth stage, so a farmer gets "your wheat is at high risk of heat damage this week"
instead of "38 °C and 40 mm of rain".

The same weather means different things to different crops. Wheat at flowering is far more
vulnerable to heat than wheat that has already ripened, so the score is calculated against
thresholds for that crop and that stage.

## The score is arithmetic, and the model never touches it

Five hazards are scored separately — heat, frost, excess rain, fungal disease risk, and
wind lodging — each against thresholds defined per crop and growth stage. They're combined
using stage-specific weights into a 0–100 score, a severity band, and whichever hazard
contributed most.

All of that lives in `app/domain/`, does no I/O, and is tested against hand-checked vectors.
An LLM, when one is configured, only rewrites the numbers the engine already produced into
plain advice. With no key configured, a written fallback covers the same ground and the app
works exactly as well.

That ordering is deliberate: advice about a crop is worth nothing if the number underneath
it was invented.

## When a cached score stops being true

Assessments are cached for 12 hours, but expiry isn't the only thing that can invalidate
one.

Advancing a plot's growth stage throws the cache away immediately, because the stored score
answers a question about a stage the crop has left.

If the weather provider is unreachable, a stored assessment is served with `is_stale: true`
rather than an error — you can still see last night's reading. Unless the stage has moved
on, in which case stale data would be actively misleading, and the request fails instead.

## Running it

```bash
./scripts/start.sh
```

Starts the API on port 8000 and the frontend on port 5173. `./scripts/reset.sh` wipes the
database and stops both.

By hand:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # then add your OpenWeather key
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

`JWT_SECRET` and `OPENWEATHER_API_KEY` are both needed for the app to do anything useful.
Accounts and plots work without the weather key, but scoring a plot is the whole point and
it calls OpenWeather, so without that key `/api/plots/{id}/risk` and `/api/geocode` return
503. `OPENROUTER_API_KEY` is the genuinely optional one.

```bash
cd backend && source .venv/bin/activate && pytest
cd frontend && npm test
```

The backend tests cover the scoring engine against known vectors, the caching and
stale-serving rules, and per-user isolation on the API. The frontend tests cover the score
badge, the crop/stage dialog, and error rendering.

```
backend/app/
  domain/crops.py       crop and growth-stage thresholds
  domain/engine.py      hazard scoring, no I/O
  services/weather.py   OpenWeather client
  services/advisory.py  LLM advice with deterministic fallback
  services/assessment.py  caching and stale-serving rules
  routes/               auth, plots, risk, lookup
frontend/src/
  pages/                dashboard, plot detail, login
  components/           score badge, hazard bars, forecast chart
```

## What the thresholds are actually worth

Six crops, five stages each, with thresholds I compiled from agronomic references rather
than from field trials. The model is plausible, not validated, and I would not want a real
planting decision made on it without an agronomist checking the numbers first.

Forecasts are five days, so it says nothing about the season. Growth stage is set by hand;
the app has no way to tell whether a plot has actually reached the stage it's been told
about.

## License

[MIT](LICENSE)
