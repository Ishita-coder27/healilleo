"""
backend/app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import users, medical_reports, auth
from app.api.routes import appointments, medications
from contextlib import asynccontextmanager
from app.scheduler import start_scheduler

import app.models

@asynccontextmanager
async def lifespan(app):
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()

app = FastAPI(title="Heallio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174", 
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5175",      
        "http://127.0.0.1:5175"
    ],   # Vite dev server + React defaults
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(medical_reports.router)
app.include_router(appointments.router)
app.include_router(medications.router)

@app.get("/health-check")
def health_check():
    return {"status": "ok"}



