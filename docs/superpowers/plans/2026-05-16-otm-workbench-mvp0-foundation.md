# OTM Workbench MVP 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend/API foundation for `otm-workbench` MVP 0.

**Architecture:** Implement a backend-first local-first modular monolith. FastAPI exposes `/api/v1/platform/*`, SQLite stores platform state, SQLAlchemy owns persistence, Alembic owns migrations, and pytest protects contracts before any final UI work begins.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, SQLite, passlib/bcrypt, pytest, httpx TestClient.

---

## Implementation Decisions

- Dependency manager: `pyproject.toml` with standard `pip install -e ".[dev]"`.
- Session model: server-side session table with bearer token returned by login.
- Bootstrap method: CLI command `python -m otm_workbench.cli bootstrap-admin`.
- Artifact root: `var/artifacts`, configurable through `OTM_ARTIFACT_ROOT`.
- Frontend in MVP 0: none. API and Swagger/OpenAPI are the validation surface.

## File Structure

- Create: `pyproject.toml` for package metadata and dependencies.
- Create: `README.md` for local setup and MVP 0 command surface.
- Create: `src/otm_workbench/main.py` for FastAPI app factory.
- Create: `src/otm_workbench/config.py` for settings.
- Create: `src/otm_workbench/contracts.py` for standard API response/error models.
- Create: `src/otm_workbench/database.py` for SQLAlchemy engine/session/base.
- Create: `src/otm_workbench/models.py` for MVP 0 platform tables.
- Create: `src/otm_workbench/security.py` for password hashing and token generation.
- Create: `src/otm_workbench/dependencies.py` for auth/capability route guards.
- Create: `src/otm_workbench/cli.py` for bootstrap admin.
- Create: `src/otm_workbench/platform/routes.py` for platform API routes.
- Create: `src/otm_workbench/platform/services.py` for platform operations.
- Create: `src/otm_workbench/platform/navigation.py` for backend-owned navigation.
- Create: `src/otm_workbench/platform/audit.py` for audit helpers.
- Create: `alembic.ini`, `migrations/env.py`, and `migrations/versions/0001_mvp0_foundation.py`.
- Create: `tests/conftest.py` for isolated test database setup.
- Create: focused test files under `tests/`.

## Task 1: Project Bootstrap And Health Contract

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/otm_workbench/__init__.py`
- Create: `src/otm_workbench/main.py`
- Create: `src/otm_workbench/config.py`
- Create: `src/otm_workbench/contracts.py`
- Create: `tests/conftest.py`
- Create: `tests/test_health.py`

- [ ] **Step 1: Write the failing health test**

```python
# tests/test_health.py
def test_health_returns_application_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "otm-workbench",
        "database": "not_configured",
    }
```

- [ ] **Step 2: Write the failing test fixture**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from otm_workbench.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())
```

- [ ] **Step 3: Run the health test to verify it fails**

Run: `python -m pytest tests/test_health.py -q`

Expected: FAIL with an import error for `otm_workbench` or missing `create_app`.

- [ ] **Step 4: Add package metadata**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "otm-workbench"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.13",
  "bcrypt>=4.1",
  "fastapi>=0.111",
  "httpx>=0.27",
  "passlib[bcrypt]>=1.7",
  "pydantic>=2.7",
  "pydantic-settings>=2.3",
  "python-multipart>=0.0.9",
  "sqlalchemy>=2.0",
  "uvicorn[standard]>=0.30",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
  "pytest-cov>=5.0",
  "ruff>=0.5",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 5: Add configuration and contracts**

```python
# src/otm_workbench/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```python
# src/otm_workbench/config.py
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "otm-workbench"
    database_url: str = "sqlite:///./var/otm_workbench.db"
    artifact_root: Path = Path("var/artifacts")
    session_ttl_minutes: int = 480

    model_config = SettingsConfigDict(env_prefix="OTM_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```python
# src/otm_workbench/contracts.py
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 50
```

- [ ] **Step 6: Add the FastAPI app factory**

```python
# src/otm_workbench/main.py
from fastapi import FastAPI

from otm_workbench.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OTM Workbench", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "database": "not_configured",
        }

    return app


app = create_app()
```

- [ ] **Step 7: Add local setup documentation**

```markdown
# otm-workbench

Local-first workbench for Oracle Transportation Management implementation projects.

## MVP 0 Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn otm_workbench.main:app --reload
```

The MVP 0 surface is backend/API-only.
```

- [ ] **Step 8: Run the health test to verify it passes**

Run: `python -m pytest tests/test_health.py -q`

Expected: PASS with `1 passed`.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml README.md src tests
git commit -m "feat: bootstrap backend health contract"
```

## Task 2: Database Core And Migration Baseline

**Files:**
- Create: `src/otm_workbench/database.py`
- Create: `src/otm_workbench/models.py`
- Modify: `src/otm_workbench/main.py`
- Modify: `tests/conftest.py`
- Create: `tests/test_database.py`
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/versions/0001_mvp0_foundation.py`

- [ ] **Step 1: Write failing database tests**

```python
# tests/test_database.py
from sqlalchemy import text

from otm_workbench.database import Base, engine, session_scope


def test_database_session_executes_sql():
    with session_scope() as session:
        result = session.execute(text("select 1")).scalar_one()

    assert result == 1


def test_metadata_contains_foundation_tables():
    table_names = set(Base.metadata.tables)

    assert "users" in table_names
    assert "workspaces" in table_names
    assert "modules" in table_names
```

- [ ] **Step 2: Run database tests to verify failure**

Run: `python -m pytest tests/test_database.py -q`

Expected: FAIL because `otm_workbench.database` does not exist.

- [ ] **Step 3: Add database session management**

```python
# src/otm_workbench/database.py
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from otm_workbench.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False}
    if get_settings().database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

- [ ] **Step 4: Add MVP 0 foundation models**

```python
# src/otm_workbench/models.py
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from otm_workbench.database import Base


def new_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class SessionToken(Base):
    __tablename__ = "session_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String)


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String)


class Environment(Base, TimestampMixin):
    __tablename__ = "environments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    environment_type: Mapped[str] = mapped_column(String, default="DEV")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)


class Capability(Base, TimestampMixin):
    __tablename__ = "capabilities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)


class UserProjectRole(Base, TimestampMixin):
    __tablename__ = "user_project_roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), index=True)


class RoleCapability(Base):
    __tablename__ = "role_capabilities"

    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    capability_id: Mapped[str] = mapped_column(ForeignKey("capabilities.id"), primary_key=True)


class Module(Base, TimestampMixin):
    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String)
    route_base: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="PLANNED")
    required_capability: Mapped[str | None] = mapped_column(String, nullable=True)
    feature_flag: Mapped[str | None] = mapped_column(String, nullable=True)
    admin_only: Mapped[bool] = mapped_column(Boolean, default=False)
    dev_only: Mapped[bool] = mapped_column(Boolean, default=False)


class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    scope: Mapped[str] = mapped_column(String, default="global")


class DomainEvent(Base, TimestampMixin):
    __tablename__ = "domain_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    event_type: Mapped[str] = mapped_column(String, index=True)
    source_module: Mapped[str] = mapped_column(String)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    aggregate_type: Mapped[str] = mapped_column(String)
    aggregate_id: Mapped[str] = mapped_column(String)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String, default="PENDING")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_type: Mapped[str] = mapped_column(String)
    source_module: Mapped[str] = mapped_column(String)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_module: Mapped[str] = mapped_column(String)
    artifact_type: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    file_name: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    sha256: Mapped[str] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column(Integer)
    sensitivity_level: Mapped[str] = mapped_column(String, default="internal")


class Manifest(Base, TimestampMixin):
    __tablename__ = "manifests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_module: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="CREATED")
    manifest_json: Mapped[str] = mapped_column(Text, default="{}")


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_module: Mapped[str] = mapped_column(String)
    evidence_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="CREATED")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(String, nullable=True)
    client_safe: Mapped[bool] = mapped_column(Boolean, default=True)
    sensitivity_level: Mapped[str] = mapped_column(String, default="client_safe")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, index=True)
    target_type: Mapped[str] = mapped_column(String)
    target_id: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
```

- [ ] **Step 5: Update health to report configured database**

```python
# src/otm_workbench/main.py
from fastapi import FastAPI
from sqlalchemy import text

from otm_workbench.config import get_settings
from otm_workbench.database import session_scope
import otm_workbench.models  # noqa: F401


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OTM Workbench", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        database_status = "ok"
        try:
            with session_scope() as session:
                session.execute(text("select 1"))
        except Exception:
            database_status = "error"
        return {
            "status": "ok" if database_status == "ok" else "degraded",
            "service": settings.service_name,
            "database": database_status,
        }

    return app


app = create_app()
```

- [ ] **Step 6: Update the health test expected database status**

```python
# tests/test_health.py
def test_health_returns_application_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "otm-workbench",
        "database": "ok",
    }
```

- [ ] **Step 7: Add Alembic baseline**

```ini
# alembic.ini
[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///./var/otm_workbench.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

```python
# migrations/env.py
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from otm_workbench.database import Base
import otm_workbench.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

For `migrations/versions/0001_mvp0_foundation.py`, generate the migration with:

Run: `python -m alembic revision --autogenerate -m "mvp0 foundation"`

Expected: a migration file containing `op.create_table` calls for the MVP 0 tables listed in `models.py`.

- [ ] **Step 8: Run database tests**

Run: `python -m pytest tests/test_database.py tests/test_health.py -q`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src tests alembic.ini migrations
git commit -m "feat: add database foundation models"
```

## Task 3: Auth, Sessions, RBAC, And Capabilities

**Files:**
- Create: `src/otm_workbench/security.py`
- Create: `src/otm_workbench/dependencies.py`
- Create: `src/otm_workbench/cli.py`
- Modify: `src/otm_workbench/platform/routes.py`
- Modify: `src/otm_workbench/main.py`
- Create: `tests/test_auth_permissions.py`

- [ ] **Step 1: Write failing permission tests**

```python
# tests/test_auth_permissions.py
def test_current_user_requires_session(client):
    response = client.get("/api/v1/platform/session/me")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_login_returns_token_after_bootstrap(client, db_session):
    from otm_workbench.platform.services import bootstrap_admin

    bootstrap_admin(db_session, email="admin@example.com", password="ChangeMe123!")

    response = client.post(
        "/api/v1/platform/session/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_capability_guard_returns_403_without_capability(client, auth_header):
    response = client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=auth_header,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
```

- [ ] **Step 2: Run permission tests to verify failure**

Run: `python -m pytest tests/test_auth_permissions.py -q`

Expected: FAIL because auth routes and fixtures do not exist.

- [ ] **Step 3: Add security helpers**

```python
# src/otm_workbench/security.py
from datetime import datetime, timedelta
from secrets import token_urlsafe

from passlib.context import CryptContext

from otm_workbench.config import get_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def new_session_token() -> str:
    return token_urlsafe(32)


def session_expiry() -> datetime:
    return datetime.utcnow() + timedelta(minutes=get_settings().session_ttl_minutes)
```

- [ ] **Step 4: Add auth dependencies**

```python
# src/otm_workbench/dependencies.py
from collections.abc import Callable
from datetime import datetime

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from otm_workbench.database import SessionLocal
from otm_workbench.models import SessionToken, User


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def require_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise api_error(401, "UNAUTHENTICATED", "A bearer token is required.")
    token_value = authorization.split(" ", 1)[1]
    token = db.get(SessionToken, token_value)
    if not token or token.revoked_at or token.expires_at <= datetime.utcnow():
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
```

- [ ] **Step 5: Add bootstrap and login services**

```python
# src/otm_workbench/platform/services.py
from sqlalchemy import select
from sqlalchemy.orm import Session

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
```

- [ ] **Step 6: Add session routes**

```python
# src/otm_workbench/platform/routes.py
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import User
from otm_workbench.platform.services import authenticate, create_session

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool


@router.post("/session/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(db, payload.email, payload.password)
    if not user:
        raise api_error(401, "UNAUTHENTICATED", "Invalid email or password.")
    session = create_session(db, user)
    return TokenResponse(access_token=session.token)


@router.get("/session/me", response_model=CurrentUserResponse)
def me(user: User = Depends(require_user)) -> CurrentUserResponse:
    return CurrentUserResponse(id=user.id, email=user.email, is_admin=user.is_admin)
```

- [ ] **Step 7: Register platform router in the app**

```python
# src/otm_workbench/main.py
from fastapi import FastAPI
from sqlalchemy import text

from otm_workbench.config import get_settings
from otm_workbench.database import session_scope
from otm_workbench.platform.routes import router as platform_router
import otm_workbench.models  # noqa: F401


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OTM Workbench", version="0.1.0")
    app.include_router(platform_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        database_status = "ok"
        try:
            with session_scope() as session:
                session.execute(text("select 1"))
        except Exception:
            database_status = "error"
        return {"status": "ok" if database_status == "ok" else "degraded", "service": settings.service_name, "database": database_status}

    return app


app = create_app()
```

- [ ] **Step 8: Add CLI bootstrap**

```python
# src/otm_workbench/cli.py
import argparse

from otm_workbench.database import session_scope
from otm_workbench.platform.services import bootstrap_admin


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap = subparsers.add_parser("bootstrap-admin")
    bootstrap.add_argument("--email", required=True)
    bootstrap.add_argument("--password", required=True)
    args = parser.parse_args()

    if args.command == "bootstrap-admin":
        with session_scope() as db:
            user = bootstrap_admin(db, email=args.email, password=args.password)
        print(f"Admin user ready: {user.email}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 9: Update `tests/conftest.py` with database isolation and auth header**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from otm_workbench.database import Base, SessionLocal, engine
from otm_workbench.main import create_app
from otm_workbench.platform.services import bootstrap_admin, create_session


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_header(db_session):
    user = bootstrap_admin(db_session, email="user@example.com", password="ChangeMe123!")
    user.is_admin = False
    db_session.commit()
    session = create_session(db_session, user)
    return {"Authorization": f"Bearer {session.token}"}
```

- [ ] **Step 10: Run auth tests**

Run: `python -m pytest tests/test_auth_permissions.py -q`

Expected: PASS except the feature flag route test may still fail with 404 until Task 5. Keep that test marked for Task 5 by splitting it into `tests/test_feature_flags.py` when implementing.

- [ ] **Step 11: Commit**

```bash
git add src tests
git commit -m "feat: add local auth and session guards"
```

## Task 4: Workspace, Project, Profile, And Environment APIs

**Files:**
- Modify: `src/otm_workbench/platform/routes.py`
- Modify: `src/otm_workbench/platform/services.py`
- Create: `tests/test_operational_context.py`

- [ ] **Step 1: Write failing operational context tests**

```python
# tests/test_operational_context.py
def test_create_workspace_project_profile_environment(client, admin_header):
    workspace = client.post("/api/v1/platform/workspaces", json={"name": "Local"}, headers=admin_header)
    assert workspace.status_code == 200

    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace.json()["id"], "name": "OTM Rollout"},
        headers=admin_header,
    )
    assert project.status_code == 200

    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project.json()["id"], "name": "Default"},
        headers=admin_header,
    )
    assert profile.status_code == 200

    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project.json()["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    )
    assert environment.status_code == 200


def test_workspace_list_requires_authentication(client):
    response = client.get("/api/v1/platform/workspaces")

    assert response.status_code == 401
```

- [ ] **Step 2: Add `admin_header` fixture**

```python
# tests/conftest.py
@pytest.fixture
def admin_header(db_session):
    user = bootstrap_admin(db_session, email="admin@example.com", password="ChangeMe123!")
    session = create_session(db_session, user)
    return {"Authorization": f"Bearer {session.token}"}
```

- [ ] **Step 3: Run context tests to verify failure**

Run: `python -m pytest tests/test_operational_context.py -q`

Expected: FAIL with 404 for missing operational context routes.

- [ ] **Step 4: Add schemas and routes**

Add these request/response models and routes to `src/otm_workbench/platform/routes.py`:

```python
class WorkspaceCreate(BaseModel):
    name: str


class ProjectCreate(BaseModel):
    workspace_id: str
    name: str


class ProfileCreate(BaseModel):
    project_id: str
    name: str


class EnvironmentCreate(BaseModel):
    project_id: str
    name: str
    environment_type: str = "DEV"


class IdNameResponse(BaseModel):
    id: str
    name: str


@router.post("/workspaces", response_model=IdNameResponse)
def create_workspace(payload: WorkspaceCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    workspace = Workspace(name=payload.name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return IdNameResponse(id=workspace.id, name=workspace.name)


@router.get("/workspaces", response_model=list[IdNameResponse])
def list_workspaces(db: Session = Depends(get_db), user: User = Depends(require_user)):
    return [IdNameResponse(id=item.id, name=item.name) for item in db.query(Workspace).all()]


@router.post("/projects", response_model=IdNameResponse)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    project = Project(workspace_id=payload.workspace_id, name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return IdNameResponse(id=project.id, name=project.name)


@router.post("/profiles", response_model=IdNameResponse)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    profile = Profile(project_id=payload.project_id, name=payload.name)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return IdNameResponse(id=profile.id, name=profile.name)


@router.post("/environments", response_model=IdNameResponse)
def create_environment(payload: EnvironmentCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    environment = Environment(project_id=payload.project_id, name=payload.name, environment_type=payload.environment_type)
    db.add(environment)
    db.commit()
    db.refresh(environment)
    return IdNameResponse(id=environment.id, name=environment.name)
```

Also import `Workspace`, `Project`, `Profile`, and `Environment` from `otm_workbench.models`.

- [ ] **Step 5: Run context tests**

Run: `python -m pytest tests/test_operational_context.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add operational context APIs"
```

## Task 5: Module Registry, Feature Flags, And Navigation

**Files:**
- Create: `src/otm_workbench/platform/navigation.py`
- Modify: `src/otm_workbench/platform/routes.py`
- Create: `tests/test_modules_navigation.py`

- [ ] **Step 1: Write failing module and navigation tests**

```python
# tests/test_modules_navigation.py
def test_modules_endpoint_returns_registered_master_data(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "master_data"
    assert response.json()["items"][0]["status"] == "PLANNED"


def test_navigation_hides_dev_only_when_flag_is_disabled(client, admin_header):
    response = client.get("/api/v1/platform/navigation", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "dev_tools" not in module_ids


def test_feature_flag_can_enable_dev_module_for_admin(client, admin_header):
    flag = client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )
    assert flag.status_code == 200

    response = client.get("/api/v1/platform/navigation", headers=admin_header)
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "dev_tools" in module_ids
```

- [ ] **Step 2: Run module tests to verify failure**

Run: `python -m pytest tests/test_modules_navigation.py -q`

Expected: FAIL with 404 for missing routes.

- [ ] **Step 3: Add navigation builder**

```python
# src/otm_workbench/platform/navigation.py
from sqlalchemy.orm import Session

from otm_workbench.models import FeatureFlag, Module, User


def seed_modules(db: Session) -> None:
    modules = [
        Module(id="home", display_name="Project Cockpit", route_base="/home", status="ACTIVE"),
        Module(id="master_data", display_name="Data Factory", route_base="/master-data", status="PLANNED"),
        Module(id="evidence", display_name="Evidence Hub", route_base="/evidence", status="PLANNED"),
        Module(id="admin", display_name="Admin Console", route_base="/admin", status="PLANNED", admin_only=True),
        Module(id="dev_tools", display_name="Developer Tools", route_base="/dev-tools", status="PLANNED", dev_only=True, feature_flag="dev_tools"),
    ]
    for module in modules:
        if not db.get(Module, module.id):
            db.add(module)
    db.commit()


def flag_enabled(db: Session, name: str | None) -> bool:
    if not name:
        return True
    flag = db.query(FeatureFlag).filter(FeatureFlag.name == name).first()
    return bool(flag and flag.enabled)


def navigation_items(db: Session, user: User) -> list[dict[str, str]]:
    seed_modules(db)
    items = []
    for module in db.query(Module).order_by(Module.display_name).all():
        if module.admin_only and not user.is_admin:
            continue
        if module.dev_only and (not user.is_admin or not flag_enabled(db, module.feature_flag)):
            continue
        if not flag_enabled(db, module.feature_flag):
            continue
        items.append({"id": module.id, "label": module.display_name, "path": module.route_base, "status": module.status})
    return items
```

- [ ] **Step 4: Add routes for modules, navigation, and feature flags**

Add to `src/otm_workbench/platform/routes.py`:

```python
from otm_workbench.contracts import PageResponse
from otm_workbench.models import FeatureFlag, Module
from otm_workbench.platform.navigation import navigation_items, seed_modules


class ModuleResponse(BaseModel):
    id: str
    display_name: str
    route_base: str
    status: str


class NavigationItem(BaseModel):
    id: str
    label: str
    path: str
    status: str


class FeatureFlagRequest(BaseModel):
    name: str
    enabled: bool
    scope: str = "global"


@router.get("/modules", response_model=PageResponse[ModuleResponse])
def list_modules(db: Session = Depends(get_db), user: User = Depends(require_user)):
    seed_modules(db)
    modules = db.query(Module).order_by(Module.display_name).all()
    items = [
        ModuleResponse(id=item.id, display_name=item.display_name, route_base=item.route_base, status=item.status)
        for item in modules
    ]
    return PageResponse(items=items, total=len(items))


@router.get("/navigation", response_model=PageResponse[NavigationItem])
def navigation(db: Session = Depends(get_db), user: User = Depends(require_user)):
    items = [NavigationItem(**item) for item in navigation_items(db, user)]
    return PageResponse(items=items, total=len(items))


@router.post("/feature-flags")
def upsert_feature_flag(
    payload: FeatureFlagRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    flag = db.query(FeatureFlag).filter(FeatureFlag.name == payload.name).first()
    if not flag:
        flag = FeatureFlag(name=payload.name, enabled=payload.enabled, scope=payload.scope)
        db.add(flag)
    else:
        flag.enabled = payload.enabled
        flag.scope = payload.scope
    db.commit()
    db.refresh(flag)
    return {"id": flag.id, "name": flag.name, "enabled": flag.enabled, "scope": flag.scope}
```

- [ ] **Step 5: Run module and navigation tests**

Run: `python -m pytest tests/test_modules_navigation.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add module registry and navigation"
```

## Task 6: Jobs, Artifacts, Manifests, Evidence, And Audit

**Files:**
- Create: `src/otm_workbench/platform/audit.py`
- Modify: `src/otm_workbench/platform/routes.py`
- Modify: `src/otm_workbench/platform/services.py`
- Create: `tests/test_operational_metadata.py`

- [ ] **Step 1: Write failing operational metadata tests**

```python
# tests/test_operational_metadata.py
def test_create_job(client, admin_header):
    response = client.post(
        "/api/v1/platform/jobs",
        json={"job_type": "health_check", "source_module": "platform", "input_json": "{}"},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"


def test_artifact_hash_metadata_and_evidence_are_client_safe(client, admin_header, tmp_path):
    artifact_file = tmp_path / "sample.txt"
    artifact_file.write_text("safe sample", encoding="utf-8")

    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "platform",
            "artifact_type": "sample",
            "file_path": str(artifact_file),
            "file_name": "sample.txt",
            "content_type": "text/plain",
            "sensitivity_level": "internal",
        },
        headers=admin_header,
    )
    assert artifact.status_code == 200
    assert len(artifact.json()["sha256"]) == 64

    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "platform",
            "evidence_type": "sample",
            "summary_json": "{\"status\":\"ok\"}",
            "artifact_id": artifact.json()["id"],
        },
        headers=admin_header,
    )
    assert evidence.status_code == 200
    assert evidence.json()["client_safe"] is True
    assert "safe sample" not in str(evidence.json())


def test_audit_log_records_feature_flag_change(client, admin_header):
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/audit-logs", headers=admin_header)
    assert response.status_code == 200
    assert any(item["action"] == "feature_flag.upsert" for item in response.json()["items"])
```

- [ ] **Step 2: Run metadata tests to verify failure**

Run: `python -m pytest tests/test_operational_metadata.py -q`

Expected: FAIL with 404 for missing jobs/artifacts/evidence/audit routes.

- [ ] **Step 3: Add audit helper**

```python
# src/otm_workbench/platform/audit.py
from sqlalchemy.orm import Session

from otm_workbench.models import AuditLog, User


def write_audit(
    db: Session,
    actor: User | None,
    action: str,
    target_type: str,
    target_id: str | None = None,
    metadata_json: str = "{}",
) -> AuditLog:
    record = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata_json,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
```

- [ ] **Step 4: Add hash helper**

Add to `src/otm_workbench/platform/services.py`:

```python
from pathlib import Path
from hashlib import sha256


def file_sha256(path: str) -> tuple[str, int]:
    data = Path(path).read_bytes()
    return sha256(data).hexdigest(), len(data)
```

- [ ] **Step 5: Add metadata routes**

Add to `src/otm_workbench/platform/routes.py`:

```python
from otm_workbench.models import Artifact, AuditLog, Evidence, Job, Manifest
from otm_workbench.platform.audit import write_audit
from otm_workbench.platform.services import file_sha256


class JobCreate(BaseModel):
    job_type: str
    source_module: str
    input_json: str = "{}"


class ArtifactCreate(BaseModel):
    source_module: str
    artifact_type: str
    file_path: str
    file_name: str
    content_type: str
    sensitivity_level: str = "internal"


class ManifestCreate(BaseModel):
    source_module: str
    manifest_json: str
    status: str = "CREATED"


class EvidenceCreate(BaseModel):
    source_module: str
    evidence_type: str
    summary_json: str
    artifact_id: str | None = None
    manifest_id: str | None = None


@router.post("/jobs")
def create_job(payload: JobCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = Job(job_type=payload.job_type, source_module=payload.source_module, input_json=payload.input_json)
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"id": job.id, "status": job.status}


@router.post("/artifacts")
def create_artifact(payload: ArtifactCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    digest, size = file_sha256(payload.file_path)
    artifact = Artifact(
        source_module=payload.source_module,
        artifact_type=payload.artifact_type,
        file_path=payload.file_path,
        file_name=payload.file_name,
        content_type=payload.content_type,
        sha256=digest,
        size_bytes=size,
        sensitivity_level=payload.sensitivity_level,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return {"id": artifact.id, "sha256": artifact.sha256, "size_bytes": artifact.size_bytes}


@router.post("/manifests")
def create_manifest(payload: ManifestCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    manifest = Manifest(source_module=payload.source_module, manifest_json=payload.manifest_json, status=payload.status)
    db.add(manifest)
    db.commit()
    db.refresh(manifest)
    return {"id": manifest.id, "status": manifest.status}


@router.post("/evidence")
def create_evidence(payload: EvidenceCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    evidence = Evidence(
        source_module=payload.source_module,
        evidence_type=payload.evidence_type,
        summary_json=payload.summary_json,
        artifact_id=payload.artifact_id,
        manifest_id=payload.manifest_id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return {"id": evidence.id, "client_safe": evidence.client_safe, "status": evidence.status}


@router.get("/audit-logs")
def list_audit_logs(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    items = [{"id": item.id, "action": item.action, "target_type": item.target_type, "target_id": item.target_id} for item in logs]
    return PageResponse(items=items, total=len(items))
```

- [ ] **Step 6: Add audit call to feature flag route**

In `upsert_feature_flag`, after `db.refresh(flag)`, add:

```python
write_audit(db, user, "feature_flag.upsert", "feature_flag", flag.id)
```

- [ ] **Step 7: Run operational metadata tests**

Run: `python -m pytest tests/test_operational_metadata.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src tests
git commit -m "feat: add operational metadata APIs"
```

## Task 7: Error Normalization And Full Verification

**Files:**
- Modify: `src/otm_workbench/main.py`
- Modify: `README.md`
- Create: `tests/test_error_contracts.py`

- [ ] **Step 1: Write failing error contract tests**

```python
# tests/test_error_contracts.py
def test_404_uses_standard_error_shape(client):
    response = client.get("/missing-route")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert response.json()["message"]


def test_unauthenticated_uses_standard_error_shape(client):
    response = client.get("/api/v1/platform/workspaces")

    assert response.status_code == 401
    assert response.json() == {
        "code": "UNAUTHENTICATED",
        "message": "A bearer token is required.",
        "details": {},
    }
```

- [ ] **Step 2: Run error tests to verify failure**

Run: `python -m pytest tests/test_error_contracts.py -q`

Expected: FAIL because FastAPI default exception shape uses `detail`.

- [ ] **Step 3: Add exception handlers**

Add to `src/otm_workbench/main.py`:

```python
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
```

Inside `create_app()`, before routes return:

```python
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            payload = {"code": detail["code"], "message": detail["message"], "details": detail.get("details", {})}
        elif exc.status_code == 404:
            payload = {"code": "NOT_FOUND", "message": "The requested resource was not found.", "details": {}}
        else:
            payload = {"code": "HTTP_ERROR", "message": str(detail), "details": {}}
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"code": "VALIDATION_ERROR", "message": "The request payload is invalid.", "details": {"errors": exc.errors()}},
        )
```

- [ ] **Step 4: Update `api_error` to include `details`**

```python
# src/otm_workbench/dependencies.py
def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message, "details": {}})
```

- [ ] **Step 5: Update README with MVP 0 verification commands**

```markdown
## MVP 0 Verification

```powershell
python -m pytest
python -m alembic upgrade head
python -m uvicorn otm_workbench.main:app --reload
```
```

- [ ] **Step 6: Run the full test suite**

Run: `python -m pytest -q`

Expected: PASS for all MVP 0 tests.

- [ ] **Step 7: Run migrations**

Run: `python -m alembic upgrade head`

Expected: exit code 0 and SQLite schema at `var/otm_workbench.db`.

- [ ] **Step 8: Run lint**

Run: `python -m ruff check src tests`

Expected: exit code 0.

- [ ] **Step 9: Commit**

```bash
git add README.md src tests
git commit -m "test: normalize platform error contracts"
```

## Final Acceptance Checklist

- [ ] `python -m pytest -q` passes.
- [ ] `python -m ruff check src tests` passes.
- [ ] `python -m alembic upgrade head` passes.
- [ ] `/health` returns service and database status.
- [ ] `/api/v1/platform/session/login` returns a bearer token for a bootstrap admin.
- [ ] Anonymous users receive `401` for protected platform routes.
- [ ] Non-admin users receive `403` for admin-only platform actions.
- [ ] Workspaces, projects, profiles, and environments can be created through API tests.
- [ ] `/api/v1/platform/modules` returns registered modules.
- [ ] `/api/v1/platform/navigation` filters dev-only modules by feature flag and admin status.
- [ ] Jobs, artifacts, manifests, evidence, and audit logs can be created or queried through API tests.
- [ ] Evidence responses do not include raw artifact file contents.
- [ ] `README.md` documents setup and verification commands.

## Spec Coverage Review

- FastAPI backend baseline: Task 1.
- SQLite, SQLAlchemy, Alembic: Task 2.
- Auth, sessions, RBAC, capabilities: Task 3.
- Workspace, project, profile, environment: Task 4.
- Module registry, feature flags, navigation: Task 5.
- Jobs, artifacts, manifests, evidence, audit: Task 6.
- Error model, pytest, verification: Task 7.
- React UI, cloud sync, full Data Factory, Rates, Load Plan, Oracle Lab, and OTM Explorer are intentionally deferred to later MVPs.
