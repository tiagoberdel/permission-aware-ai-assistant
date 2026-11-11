from fastapi import APIRouter, Depends

from app.agent.service import ask_andino
from app.auth.dependencies import DemoSession, get_demo_session
from app.schemas.agent import AgentAskRequest, AgentAskResponse

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/ask", response_model=AgentAskResponse)
async def ask_agent(
    data: AgentAskRequest,
    demo_session: DemoSession = Depends(get_demo_session), 
):
    answer = await ask_andino(
        query=data.query,
        user=demo_session.user,
        conversation_id=str(demo_session.conversation_id),
    )

    return AgentAskResponse(answer=answer)