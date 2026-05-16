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


@pytest.fixture
def admin_header(db_session):
    user = bootstrap_admin(db_session, email="admin@example.com", password="ChangeMe123!")
    session = create_session(db_session, user)
    return {"Authorization": f"Bearer {session.token}"}
