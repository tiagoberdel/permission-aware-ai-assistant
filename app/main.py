from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.routers.auth import router as auth_router
from app.routers.agent import router as agent_router
from app.routers.demo import router as demo_router
from app.db import get_db

app = FastAPI()

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(demo_router)

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