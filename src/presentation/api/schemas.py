from pydantic import BaseModel, Field
class ChatRequest(BaseModel):
    text: str = Field(...)
    user_id: str = Field(...)