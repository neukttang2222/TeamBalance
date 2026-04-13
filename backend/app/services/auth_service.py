from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import pbkdf2_hmac
from hashlib import sha256
from hmac import compare_digest
from secrets import token_bytes
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models import AuthSessionRecord, UserProfileRecord
from app.schemas import (
    AuthSessionResponse,
    AuthSignupResponse,
    CurrentUserResponse,
    UserSearchItemResponse,
    UserSearchResponse,
)


SESSION_TTL_DAYS = 14


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    display_name: str | None = None


PBKDF2_ITERATIONS = 310000


def signup_user(name: str, email: str, password: str) -> AuthSignupResponse:
    normalized_email = _normalize_email(email)
    normalized_name = name.strip()
    validated_password = _validate_password(password)
    now = _now()

    with get_db_session() as session:
        user = session.execute(select(UserProfileRecord).where(UserProfileRecord.email == normalized_email)).scalars().first()
        if user is not None and user.password_hash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")

        if user is None:
            user = UserProfileRecord(
                id=str(uuid4()),
                email=normalized_email,
                display_name=normalized_name,
                password_hash=_hash_password(validated_password),
                created_at=now,
                last_login_at=None,
            )
            session.add(user)
        else:
            user.display_name = normalized_name
            user.password_hash = _hash_password(validated_password)

        session.flush()
        return AuthSignupResponse(
            message="signed up",
            user=_user_response(user),
        )


def login_with_password(email: str, password: str) -> AuthSessionResponse:
    normalized_email = _normalize_email(email)
    validated_password = _validate_password(password)
    now = _now()
    token = token_urlsafe(32)

    with get_db_session() as session:
        user = session.execute(select(UserProfileRecord).where(UserProfileRecord.email == normalized_email)).scalars().first()
        if user is None or not user.password_hash or not _verify_password(validated_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
        user.last_login_at = now

        auth_session = AuthSessionRecord(
            id=str(uuid4()),
            user_id=user.id,
            token_hash=_hash_token(token),
            created_at=now,
            expires_at=now + timedelta(days=SESSION_TTL_DAYS),
            revoked_at=None,
        )
        session.add(auth_session)
        session.flush()

        return AuthSessionResponse(
            access_token=token,
            user=_user_response(user),
        )


def get_current_user_by_token(token: str) -> CurrentUser:
    token_hash = _hash_token(token)
    now = _now()

    with get_db_session() as session:
        stmt = select(AuthSessionRecord).where(AuthSessionRecord.token_hash == token_hash)
        auth_session = session.execute(stmt).scalars().first()
        if auth_session is None or auth_session.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session")
        if _is_expired(auth_session.expires_at, now):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session expired")

        user = session.get(UserProfileRecord, auth_session.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")

        return CurrentUser(id=user.id, email=user.email, display_name=user.display_name)


def get_current_user_response(token: str) -> CurrentUserResponse:
    token_hash = _hash_token(token)
    now = _now()

    with get_db_session() as session:
        auth_session = session.execute(
            select(AuthSessionRecord).where(AuthSessionRecord.token_hash == token_hash)
        ).scalars().first()
        if auth_session is None or auth_session.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session")
        if _is_expired(auth_session.expires_at, now):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session expired")

        user = session.get(UserProfileRecord, auth_session.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
        return _user_response(user)


def logout_token(token: str) -> None:
    token_hash = _hash_token(token)

    with get_db_session() as session:
        auth_session = session.execute(
            select(AuthSessionRecord).where(AuthSessionRecord.token_hash == token_hash)
        ).scalars().first()
        if auth_session is not None and auth_session.revoked_at is None:
            auth_session.revoked_at = _now()
            session.flush()


def find_or_create_user_by_email(session: Session, email: str, display_name: str | None = None) -> UserProfileRecord:
    return _get_or_create_user(session, _normalize_email(email), display_name, _now())


def find_existing_user_by_email(session: Session, email: str) -> UserProfileRecord:
    normalized_email = _normalize_email(email)
    user = session.execute(select(UserProfileRecord).where(UserProfileRecord.email == normalized_email)).scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user


def find_existing_user_by_id(session: Session, user_id: str) -> UserProfileRecord:
    user = session.get(UserProfileRecord, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user


def search_users(query: str, *, limit: int = 10) -> UserSearchResponse:
    normalized = query.strip().lower()
    if len(normalized) < 2:
        return UserSearchResponse(users=[])

    with get_db_session() as session:
        users = session.execute(
            select(UserProfileRecord)
            .where(
                or_(
                    UserProfileRecord.email.ilike(f"%{normalized}%"),
                    UserProfileRecord.display_name.ilike(f"%{normalized}%"),
                )
            )
            .order_by(UserProfileRecord.last_login_at.desc(), UserProfileRecord.created_at.desc())
            .limit(limit)
        ).scalars().all()
        return UserSearchResponse(
            users=[
                UserSearchItemResponse(
                    user_id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                )
                for user in users
            ]
        )


def _get_or_create_user(
    session: Session,
    email: str,
    display_name: str | None,
    now: datetime,
) -> UserProfileRecord:
    user = session.execute(select(UserProfileRecord).where(UserProfileRecord.email == email)).scalars().first()
    if user is not None:
        if display_name and not user.display_name:
            user.display_name = display_name
        return user

    user = UserProfileRecord(
        id=str(uuid4()),
        email=email,
        display_name=display_name,
        created_at=now,
        last_login_at=None,
    )
    session.add(user)
    session.flush()
    return user


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="valid email is required")
    return normalized


def _validate_password(password: str) -> str:
    normalized = str(password or "")
    if len(normalized) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password must be at least 8 characters")
    return normalized


def _hash_password(password: str) -> str:
    salt = token_bytes(16)
    derived = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
    except ValueError:
        return False

    if scheme != "pbkdf2_sha256":
        return False

    derived = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return compare_digest(derived.hex(), digest_hex)


def _hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _is_expired(expires_at: datetime | None, now: datetime) -> bool:
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at < now


def _user_response(user: UserProfileRecord) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )


def _now() -> datetime:
    return datetime.now(UTC)
