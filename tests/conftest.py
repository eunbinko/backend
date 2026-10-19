import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.main import create_app


@pytest.fixture
def database_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    yield engine
    engine.dispose()


@pytest.fixture
def client(database_engine):
    with TestClient(create_app(database_engine)) as client:
        yield client


@pytest.fixture
def signup_data():
    return {"email": "member@example.com", "password": "secret-password!", "name": "회원"}
