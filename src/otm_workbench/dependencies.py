from collections.abc import Callable, Iterator
from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from otm_workbench.database import SessionLocal
from otm_workbench.models import SessionToken, User


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def api_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details or {}},
    )


def require_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise api_error(401, "UNAUTHENTICATED", "A bearer token is required.")
    token_value = authorization.split(" ", 1)[1]
    token = db.get(SessionToken, token_value)
    if not token or token.revoked_at or token.expires_at <= datetime.now(UTC).replace(tzinfo=None):
        raise api_error(401, "UNAUTHENTICATED", "The session is invalid or expired.")
    user = db.get(User, token.user_id)
    if not user or not user.is_active:
        raise api_error(401, "UNAUTHENTICATED", "The user is inactive.")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise api_error(403, "FORBIDDEN", "Admin access is required.")
    return user


def require_capability(capability: str) -> Callable[[User], User]:
    def dependency(user: User = Depends(require_user)) -> User:
        if user.is_admin:
            return user
        raise api_error(403, "FORBIDDEN", f"Capability is required: {capability}")

    return dependency
