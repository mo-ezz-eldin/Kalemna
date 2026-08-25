from pydantic import BaseModel, Field , EmailStr
class ChatRequest(BaseModel):
    text: str = Field(...)



class Token_Data(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field(...)


class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="يجب أن يكون بين 3 و 50 حرف")
    password: str = Field(..., min_length=6, description="الباسوورد لا يقل عن 6 حروف")
    email: EmailStr = Field(..., description="يتحقق من صيغة الإيميل تلقائياً")
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$", description="يسمح بأرقام فقط مع علامة + اختيارية")
    default_address: str = Field(default='NO_address')
