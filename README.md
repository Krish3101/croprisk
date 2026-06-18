# KisanAI - Smart Farming Assistant (V1.1)

KisanAI is a full-stack platform providing weather forecasts, market prices, and AI-driven farming assistance tools for modern agriculture. This **Version 1.1** release stabilizes the core architecture, introduces strict data isolation (multi-tenancy), enforces API security via JWT, replaces blocking synchronous network calls with asynchronous handlers, and brings the endpoints into REST compliance.

---

## 🔧 Prerequisites

You need **Python (Backend)** and **Node.js (Frontend)** installed.

```bash
python --version   # Expected: Python 3.11 or higher
node -v          # Expected: v18.0.0 or higher
```

---

## ⚙️ Environment Configuration

Before starting, configure your backend environment variables.
Create a `.env` file inside the `backend/` directory:

```env
# backend/.env
SECRET_KEY=your_super_secret_jwt_key
OPENWEATHER_KEY=your_openweather_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
INDIA_GOV_API_KEY=your_data_gov_in_api_key_here
```

*(Note: If API keys are missing, the system handles errors gracefully instead of falling back to fake data).*

---

## 🚀 How to Run

Open two separate terminal windows.

**Terminal 1 (Backend):**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

Once running:
- **Frontend App:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## 🧪 Running Tests

V1.1 introduces a comprehensive `pytest` suite for the backend to ensure API security and data isolation:

```bash
cd backend
# Make sure your virtual environment is activated
PYTHONPATH=. pytest tests/
```

---

## 📁 Project Structure

```text
kisan-ai/
├── backend/          # FastAPI Python Server
│   ├── main.py       # API Entry Point
│   ├── routes/       # API Endpoints (Secured via JWT)
│   ├── services/     # Async Business Logic & Integrations
│   ├── models/       # SQLAlchemy Database Models & Pydantic DTOs
│   ├── tests/        # Pytest integration tests
│   └── requirements.txt
├── frontend/         # React + Vite Client
│   ├── src/          # Source Code (Components, Pages, Hooks)
│   ├── package.json  # Dependencies
│   └── vite.config.js
├── README.md         # Documentation
└── .gitignore        # Git tracking rules
```

---

## 🛡️ V1.1 Security & Architecture Notes
* **Data Isolation:** All crops, expenses, and soil reports are strictly bound to a `user_id`.
* **Async Network I/O:** The server no longer blocks when contacting external APIs (OpenWeather, OpenRouter), preventing DoS under load.
* **REST Integrity:** Route structures enforce HTTP standards (e.g., `DELETE /crops/{id}`).
* **Database:** Uses a localized `kisanai.db` SQLite file for zero-config startup. Auto-migrates tables on boot.
