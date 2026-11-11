from fastapi import APIRouter, Depends, HTTPException, status
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.demo import DemoSessionRequest, DemoSessionResponse
from app.services.demo import resolve_demo_user
from app.auth.jwt import create_access_token

router = APIRouter(prefix="/demo", tags=["demo"])

@router.post("/sessions", response_model=DemoSessionResponse)
def create_demo_session(data: DemoSessionRequest, db: Session = Depends(get_db)):
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