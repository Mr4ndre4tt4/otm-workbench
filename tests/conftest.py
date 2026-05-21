import os
from pathlib import Path
from tempfile import gettempdir

import pytest
from fastapi.testclient import TestClient

_TEST_DATABASE_PATH: Path | None = None


def _configure_test_database_url() -> None:
    global _TEST_DATABASE_PATH
    if os.environ.get("OTM_DATABASE_URL"):
        return

    worker = os.environ.get("PYTEST_XDIST_WORKER", "local")
    database_dir = Path(gettempdir()) / "otm_workbench_tests"
    database_dir.mkdir(parents=True, exist_ok=True)
    _TEST_DATABASE_PATH = database_dir / f"{worker}_{os.getpid()}.db"
    os.environ["OTM_DATABASE_URL"] = f"sqlite:///{_TEST_DATABASE_PATH.as_posix()}"


_configure_test_database_url()

from otm_workbench.database import Base, SessionLocal, engine  # noqa: E402
from otm_workbench.main import create_app  # noqa: E402
from otm_workbench.platform.services import bootstrap_admin, create_session  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def pytest_sessionfinish(session, exitstatus):
    if _TEST_DATABASE_PATH is None:
        return
    engine.dispose()
    try:
        _TEST_DATABASE_PATH.unlink()
    except FileNotFoundError:
        return


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


@pytest.fixture
def admin_header(db_session):
    user = bootstrap_admin(db_session, email="admin@example.com", password="ChangeMe123!")
    session = create_session(db_session, user)
    return {"Authorization": f"Bearer {session.token}"}
