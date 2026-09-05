from pydantic import BaseModel, ConfigDict, Field


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


class AdminSessionResponse(BaseModel):
    authenticated: bool


class AdminLoginResponse(AdminSessionResponse):
    username: str
