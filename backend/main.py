from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.database import init_db
from routes import auth, plots, risk

app = FastAPI(title="KisanAI Risk Intelligence V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth.router)
app.include_router(plots.router)
app.include_router(risk.router)

@app.get("/")
def health_check():
    return {"status": "KisanAI Risk Intelligence V2 running"}
