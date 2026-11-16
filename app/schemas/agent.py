from pydantic import BaseModel, Field

class AgentAskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1500)

class AgentAskResponse(BaseModel):
    answer: str