import pytest
from fastapi.testclient import TestClient

from otm_workbench.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())
