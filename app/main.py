from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "result": result.scalar()
        }