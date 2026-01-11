from fastapi import FastAPI
from app.api.routes import users

app = FastAPI()

@app.get("/health-check")
def health_check():
    return {"status": "ok"}

@app.get("/db-test")
def db_test():
    return {"db": "connected"}

app.include_router(users.router)
