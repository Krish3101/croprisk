# KisanAI Risk Intelligence Platform V2

KisanAI Risk Intelligence Platform is an AI-driven web application designed to help farmers identify crop risks early. Unlike generic dashboards, this V2 focuses exclusively on predictive agronomy—correlating specific crop growth stages with 5-day weather forecasts to generate actionable risk assessments.

---

## 🎯 Core Problem Solved
Generic weather apps say "It will rain." KisanAI says "It will rain, and your Tomatoes in the Flowering stage are at 85% risk for Late Blight. Apply fungicide today."

## 🚀 Features
- **Plot Management:** Track multiple plots by crop type, location, and growth stage.
- **Deterministic Risk Engine:** A rule-based scoring engine (0-100) evaluating Heavy Rain, High Humidity, Extreme Temps, and Storm Conditions.
- **AI Risk Analysis:** Structured, actionable explanations using OpenRouter LLM based purely on deterministic scores.
- **Triage Dashboard:** A clean UI prioritizing plots by risk severity (LOW, MODERATE, HIGH).
- **Secure Architecture:** Multi-tenant FastAPI backend with JWT-protected data isolation.

---

## ⚙️ Tech Stack
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React 19, Vite, Tailwind CSS v4
- **External APIs:** OpenWeatherMap, OpenRouter

---

## 🔧 Setup & Installation

### 1. Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
# backend/.env
SECRET_KEY=your_super_secret_jwt_key
OPENWEATHER_KEY=your_openweather_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

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
