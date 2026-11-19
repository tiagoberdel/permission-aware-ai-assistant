import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.agent.sessions import purge_expired
from app.routers.auth import router as auth_router
from app.routers.agent import router as agent_router
from app.routers.demo import router as demo_router
from app.db import get_db
from app.limiter import limiter


async def session_cleanup_loop():
    while True:
        await asyncio.sleep(60)
        purge_expired()


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(session_cleanup_loop())

    try:
        yield
    finally:
        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(demo_router)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded, _rate_limit_exceeded_handler
)

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