from hashlib import sha256
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.models import SessionToken, User
from otm_workbench.security import hash_password, new_session_token, session_expiry, verify_password


def bootstrap_admin(db: Session, email: str, password: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        return existing
    user = User(email=email, password_hash=hash_password(password), is_admin=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user: User) -> SessionToken:
    session = SessionToken(token=new_session_token(), user_id=user.id, expires_at=session_expiry())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def file_sha256(path: str) -> tuple[str, int]:
    data = Path(path).read_bytes()
    return sha256(data).hexdigest(), len(data)


def resolve_artifact_storage_path(path: str | Path) -> Path:
    artifact_root = get_settings().artifact_root.resolve()
    candidate = Path(path).resolve()
    try:
        candidate.relative_to(artifact_root)
    except ValueError as exc:
        raise ValueError("Artifact file must be inside the configured artifact root.") from exc
    return candidate
