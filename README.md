# CropRisk

The same weather is not the same risk for every field: a 35 °C heat wave means grain loss for wheat that is flowering and very little for wheat that has already ripened. CropRisk scores the 5-day forecast for one plot's crop and growth stage into a risk from 0 to 100 across five hazards, names the main hazard, and explains the result in plain words.

![screenshot](screenshot.png)

## Run (macOS)

Needs uv and Node.js 22 or newer (`brew install uv node`) and a free OpenWeather key; an OpenRouter key is optional.

```bash
# terminal 1
cd backend
cp .env.example .env              # then add OPENWEATHER_API_KEY
uv sync --extra dev
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# terminal 2
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

Open <http://localhost:5173> and add a plot. Vite forwards `/api` to the backend.

## How it works

1. The plot page calls `GET /api/plots/{id}/assessment`.
2. If the stored assessment is for the same location and stage and its forecast is under 12 hours old, it is returned as it is.
3. Otherwise `weather.py` fetches the 5-day forecast from OpenWeather: 40 intervals of 3 hours.
4. `engine.py` reads the stage's thresholds from `crops.yaml` and scores five hazards from 0 to 100. The score is the larger of the stage-weighted sum and the single worst hazard, so one severe hazard is not averaged away: LOW is 0 to 29, MODERATE 30 to 65, HIGH 66 to 100.
5. `advisory.py` writes the explanation: fixed text for LOW, otherwise an LLM given only the finished numbers (its reply must match a fixed JSON shape), or rule-based text when there is no key or the call fails.
6. The assessment is stored and returned; the page draws the hazard bars and the forecast against the stage's thresholds.

| Hazard | What the engine looks at |
| --- | --- |
| Heat | How far and for how long temperatures go above the stage's critical heat |
| Frost | The lowest temperature against the stage's frost threshold |
| Excess rain | The wettest rolling 24 hours |
| Fungal disease | The longest run of humid hours inside the crop's disease temperature band, counted from 12 hours |
| Wind lodging | The strongest wind or gust |

Example: wheat at flowering with one night at −1.5 °C. The stage's frost threshold is 1.0 °C, so frost is the primary hazard and the score is 71, HIGH. The thresholds are indicative and not checked by an agronomist; `crops.yaml` is where verified values would go.

## API

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/health` | Server is up |
| `GET` | `/api/crops` | Crops and their growth stages, for the form |
| `GET` | `/api/geocode?q=` | Place search, for the location picker |
| `GET` | `/api/plots` | All plots with their latest score |
| `POST` | `/api/plots` | Add a plot |
| `PUT` | `/api/plots/{id}` | Edit a plot |
| `DELETE` | `/api/plots/{id}` | Delete a plot and its assessment |
| `GET` | `/api/plots/{id}/assessment` | Score, hazards, advisory and forecast; reused for up to 12 hours |
| `POST` | `/api/plots/{id}/assessment/refresh` | Fetch a new forecast and score again |

## Tests

```bash
cd backend && uv run pytest -q && cd ../frontend && npm test
```

The engine against the ten worked examples, the API with a fake forecast, and two component tests. No network.
