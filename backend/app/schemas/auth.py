from pydantic import BaseModel, Field


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class AuthSignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    created_at: str
    last_login_at: str | None = None


class UserSearchItemResponse(BaseModel):
    user_id: str
    email: str
    display_name: str | None = None


class UserSearchResponse(BaseModel):
    users: list[UserSearchItemResponse]


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUserResponse


class AuthLogoutResponse(BaseModel):
    message: str


class AuthSignupResponse(BaseModel):
    message: str
    user: CurrentUserResponse
