from fastapi import FastAPI
from app.api.routes import users, medical_reports
# , vitals, report_vitals

app = FastAPI()

@app.get("/health-check")
def health_check():
    return {"status": "ok"}

@app.get("/db-test")
def db_test():
    return {"db": "connected"}

app.include_router(users.router)
app.include_router(medical_reports.router)
# app.include_router(vitals.router)
# app.include_router(report_vitals.router)
