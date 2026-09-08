# KisanAI - Crop Risk Assessment

KisanAI combines a plot's crop and growth stage with a five-day weather forecast to produce reproducible, prioritized risk assessments and plain-language explanations for growers.

---

## 🎯 Problem Solved
Weather forecasts describe conditions but do not translate them into crop-specific, growth-stage-specific action for a particular plot. Growers need to know which of their plots is most at risk, what the primary threat is, why the forecast matters for that crop and stage, and what single action deserves attention now.

KisanAI closes that interpretation gap by evaluating five-day forecasts against deterministic agronomic rules to produce a prioritized risk assessment and plain-language explanation.

## 🚀 Features
- **Plot Management & Geocoding:** Track plots by crop type, growth stage, and location, automatically resolved to precise latitude/longitude coordinates with ambiguity clarification.
- **Deterministic Agronomic Risk Engine:** Rule-based scoring engine (0–100) evaluating 5-day forecasts against baseline agronomic rules (Heavy Precipitation, Extreme Heat, Frost Risk, High Wind, and Disease Pressure) with strict immediacy tie-breaking.
- **Severity Bands & Triage:** Clear severity levels (LOW: 0–30, MODERATE: 31–65, HIGH: 66–100) with portfolio dashboard prioritizing plots by current risk.
- **Plain-Language Analysis & Single Action:** Plain-language explanation of why identified conditions matter for the crop at its current growth stage and exactly one recommended action, with deterministic fallback if the narrative service is unavailable.
- **Freshness & Invalidation Lifecycle:** 12-hour assessment cache automatically invalidated whenever plot parameters change, plus graceful degraded operation identifying stale records during upstream weather outages.
- **Tenant Isolation:** Multi-tenant FastAPI backend ensuring growers only access their own plots and assessments.

---

## ⚙️ Tech Stack
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React 19, Vite, Tailwind CSS v4
- **External APIs:** OpenWeatherMap, OpenRouter

---

## 🔧 Setup & Installation

### 1. Environment Configuration
Copy the template environment configuration file and provide your API keys:
```bash
cp .env.example .env
```

Required variables:
- `SECRET_KEY`: Cryptographically secure secret key for JWT token signing.
- `OPENWEATHER_KEY`: (Optional) OpenWeatherMap API key for weather data.
- `OPENROUTER_API_KEY`: (Optional) OpenRouter API key for LLM risk insights.


### 2. Start Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Start Frontend
Open a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to view the application.

---

## 🧪 Testing
The backend is covered by an automated integration suite (`pytest`) testing authentication, authorization, and data isolation.
```bash
cd backend
PYTHONPATH=. pytest tests/
```
