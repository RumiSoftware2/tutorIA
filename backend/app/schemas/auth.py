from pydantic import BaseModel, Field


class TeacherLoginRequest(BaseModel):
    access_code: str = Field(min_length=1, max_length=256)


class TeacherLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
