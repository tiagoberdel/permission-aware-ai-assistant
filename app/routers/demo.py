from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from uuid import uuid4
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.db import get_db
from app.limiter import limiter
from app.schemas.demo import DemoSessionRequest, DemoSessionResponse
from app.services.demo import resolve_demo_user

router = APIRouter(prefix="/demo", tags=["demo"])

@router.post("/sessions", response_model=DemoSessionResponse)
@limiter.limit("30/hour")
def create_demo_session(
    request: Request,
    response: Response,
    data: DemoSessionRequest,
    db: Session = Depends(get_db),
):
    user = resolve_demo_user(db, data.demo_user)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo user not found."
        )
    conversation_id = str(uuid4())
    access_token = create_access_token(
        user_id=user.id,
        session_type="demo",
        conversation_id=conversation_id,
    )
    return DemoSessionResponse(
        access_token=access_token,
        conversation_id=conversation_id
    )