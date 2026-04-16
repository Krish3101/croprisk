# KisanAI - Smart Farming Assistant (V3)

KisanAI is a full-stack platform providing weather forecasts, market prices, and farming assistance tools for modern agriculture. This **Version 3** is optimized and strictly contains what's necessary to confidently run the code. 

---

## 🔧 Prerequisites Check

You need **Python (Backend)** and **Node.js (Frontend)** installed. Open your terminal (PowerShell or Command Prompt) and run these commands to check if you have them:

```powershell
python --version   # Expected: Python 3.11 or higher
node -v          # Expected: v18.0.0 or higher
npm -v           # Expected: v9.0.0 or higher
```

### What if they aren't installed?
If any of these commands fail, install them quickly using the Windows Package Manager (`winget`) by pasting these commands into PowerShell, or by visiting their official websites:

**Install Python & Node:**
```powershell
winget install -e --id Python.Python.3.11
winget install -e --id OpenJS.NodeJS
```
*(After installing, close and reopen your terminal)*

---

## 🚀 How to Run

Open two separate terminal windows (PowerShell or Command Prompt). Make sure both are opened in your `kisan-ai` folder.

**Terminal 1 (Backend):**
```powershell
cd backend
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm install
npm run dev
```

Once running:
- **Frontend App:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## 📁 Project Structure

```
kisan-ai/
├── backend/          # FastAPI Python Server
│   ├── main.py       # API Entry Point
│   ├── routes/       # API Endpoints
│   ├── models/       # Database Models
│   └── requirements.txt
├── frontend/         # React + Vite Client
│   ├── src/          # Source Code
│   ├── package.json  # Dependencies
│   └── vite.config.js
├── README.md         # You are here
└── .gitignore        # Clean commit rules
```

---

## 🛠️ Modifying the Code

The codebase has been refactored to be extremely easy to understand.
- Need to change the UI? Jump into `frontend/src/pages/` or `frontend/src/components/`.
- Need to add a new API capability? Add a route in `backend/routes/` and link it to `backend/main.py`.

Enjoy developing your Smart Farming Assistant!
