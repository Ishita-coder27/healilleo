"""
backend/app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, medical_reports, report_vitals, reports, users, vitals

app = FastAPI(
    title="AI Engine Backend",
    description="Medical AI backend — vitals extraction, reports, RAG.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,            prefix="/api")
app.include_router(users.router,           prefix="/api")
app.include_router(vitals.router,          prefix="/api")
app.include_router(medical_reports.router, prefix="/api")
app.include_router(report_vitals.router,   prefix="/api")   # handles /api/report-vitals/*
app.include_router(reports.router,         prefix="/api")   # handles /api/reports/* (public analysis/chat)


@app.get("/")
def root():
    return {"status": "ok", "message": "AI Engine Backend is running."}


@app.get("/health")
def health():
    return {"status": "healthy"}