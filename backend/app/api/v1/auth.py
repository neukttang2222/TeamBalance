from fastapi import APIRouter, Depends

from app.api.deps import get_bearer_token
from app.schemas import (
    AuthLoginRequest,
    AuthLogoutResponse,
    AuthSessionResponse,
    AuthSignupRequest,
    AuthSignupResponse,
    CurrentUserResponse,
)
from app.services.auth_service import (
    get_current_user_response,
    login_with_password,
    logout_token,
    signup_user,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthSignupResponse, status_code=201)
def signup_endpoint(payload: AuthSignupRequest) -> AuthSignupResponse:
    return signup_user(payload.name, payload.email, payload.password)


@router.post("/login", response_model=AuthSessionResponse)
def login_endpoint(payload: AuthLoginRequest) -> AuthSessionResponse:
    return login_with_password(payload.email, payload.password)


@router.post("/logout", response_model=AuthLogoutResponse)
def logout_endpoint(token: str = Depends(get_bearer_token)) -> AuthLogoutResponse:
    logout_token(token)
    return AuthLogoutResponse(message="logged out")


@router.get("/me", response_model=CurrentUserResponse)
def me_endpoint(token: str = Depends(get_bearer_token)) -> CurrentUserResponse:
    return get_current_user_response(token)
