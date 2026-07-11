from pydantic import BaseModel, Field
class ChatRequest(BaseModel):
    text: str = Field(...)