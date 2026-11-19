from fastapi import APIRouter, Depends, Request, Response

from app.agent.service import ask_andino
from app.auth.dependencies import DemoSession, get_demo_session
from app.limiter import limiter
from app.schemas.agent import AgentAskRequest, AgentAskResponse

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/ask", response_model=AgentAskResponse)
@limiter.limit("30/hour")
async def ask_agent(
    request: Request,
    response: Response,
    data: AgentAskRequest,
    demo_session: DemoSession = Depends(get_demo_session), 
):
    answer = await ask_andino(
        query=data.query,
        user=demo_session.user,
        thread_id=demo_session.thread_id,
    )

    return AgentAskResponse(answer=answer)