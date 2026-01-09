from fastapi import FastAPI

app = FastAPI(title="Hellio Health AI")

@app.get("/")
def health_check():
    return {"status": "Backend is running"}

from app.db.session import engine

@app.get("/db-test")
def db_test():
    return {"db": "connected"}
