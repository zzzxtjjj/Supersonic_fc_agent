from pydantic import BaseModel, ConfigDict, Field


class PlayerInviteResponse(BaseModel):
    player_id: str
    invite_code: str
    expires_at: str


class PlayerActivateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invite_code: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=8, max_length=128)


class PlayerActivateResponse(BaseModel):
    activated: bool


class PlayerLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class PlayerLoginResponse(BaseModel):
    authenticated: bool


class PlayerAuthUser(BaseModel):
    id: str
    player_id: str
    name: str
    photo_url: str | None = None


class PlayerMeResponse(BaseModel):
    authenticated: bool
    user: PlayerAuthUser
    is_supersonic_player: bool


class PlayerLogoutResponse(BaseModel):
    authenticated: bool
