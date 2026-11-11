from pydantic import BaseModel

class DemoSessionRequest(BaseModel):
    demo_user: str

class DemoSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    conversation_id: str
