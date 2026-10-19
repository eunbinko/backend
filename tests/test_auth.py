from concurrent.futures import ThreadPoolExecutor

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.main import create_app
from app.models.user import User


def test_signup_stores_hash_and_returns_public_fields(client, database_engine, signup_data):
    response = client.post("/user/signup", json=signup_data)
    assert response.status_code == 201
    assert response.json() == {
        "code": 201, "result": {"email": signup_data["email"], "name": signup_data["name"]}
    }
    with Session(database_engine) as session:
        user = session.scalar(select(User))
        assert user.password != signup_data["password"]
        assert verify_password(signup_data["password"], user.password)
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_duplicate_signup_does_not_overwrite_user(client, database_engine, signup_data):
    client.post("/user/signup", json=signup_data)
    response = client.post("/user/signup", json={**signup_data, "name": "다른 이름", "password": "other"})
    assert response.status_code == 409
    assert response.json()["code"] == 409
    assert isinstance(response.json()["result"], str)
    with Session(database_engine) as session:
        user = session.scalar(select(User))
        assert user.name == signup_data["name"]
        assert verify_password(signup_data["password"], user.password)
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_email_and_name_normalization(client, signup_data):
    response = client.post("/user/signup", json={**signup_data, "email": " Member@Example.COM ", "name": " 회원 "})
    assert response.status_code == 201
    assert response.json()["result"] == {"email": "member@example.com", "name": "회원"}
    assert client.post("/user/signup", json=signup_data).status_code == 409
    assert client.post("/user/login", json={**signup_data, "email": " MEMBER@example.com "}).status_code == 200


def test_login_sets_signed_expiring_httponly_cookie(client, signup_data):
    client.post("/user/signup", json=signup_data)
    response = client.post("/user/login", json={"email": signup_data["email"], "password": signup_data["password"]})
    assert response.status_code == 200
    assert response.json() == {
        "code": 200, "result": {"email": signup_data["email"], "name": signup_data["name"]}
    }
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Max-Age=1800" in cookie
    claims = jwt.decode(response.cookies["EN_AT"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert claims["sub"] == signup_data["email"]
    assert claims["exp"] - claims["iat"] == 1800


def test_secure_cookie_setting(client, signup_data, monkeypatch):
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    client.post("/user/signup", json=signup_data)
    response = client.post("/user/login", json=signup_data)
    assert "Secure" in response.headers["set-cookie"]


def test_bad_credentials_have_same_response_and_no_cookie(client, signup_data):
    client.post("/user/signup", json=signup_data)
    wrong_password = client.post("/user/login", json={**signup_data, "password": "wrong"})
    wrong_email = client.post("/user/login", json={**signup_data, "email": "missing@example.com"})
    for response in (wrong_password, wrong_email):
        assert response.status_code == 401
        assert response.json()["code"] == 401
        assert "set-cookie" not in response.headers
    assert wrong_password.json() == wrong_email.json()


@pytest.mark.parametrize("field,value", [
    ("email", "invalid"), ("email", ""), ("email", None),
    ("password", ""), ("password", None), ("password", 123), ("password", "x" * 129),
    ("name", ""), ("name", "   "), ("name", None), ("name", "x" * 101),
])
def test_invalid_signup(client, database_engine, signup_data, field, value):
    response = client.post("/user/signup", json={**signup_data, field: value})
    assert response.status_code == 422
    assert response.json()["code"] == 422
    assert signup_data["password"] not in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(User)) == 0


@pytest.mark.parametrize("field", ["email", "password", "name"])
def test_missing_signup_field(client, signup_data, field):
    del signup_data[field]
    assert client.post("/user/signup", json=signup_data).status_code == 422


@pytest.mark.parametrize("payload", [{}, {"email": "member@example.com"}, {"password": "secret"},
                                      {"email": "bad", "password": "secret"},
                                      {"email": "member@example.com", "password": ""}])
def test_invalid_login(client, payload):
    response = client.post("/user/login", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == 422
    assert "set-cookie" not in response.headers


def test_database_unique_constraint(client, database_engine, signup_data):
    client.post("/user/signup", json=signup_data)
    with Session(database_engine) as session:
        session.add(User(**signup_data))
        with pytest.raises(IntegrityError):
            session.commit()


def test_simultaneous_signup(client, database_engine, signup_data):
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: client.post("/user/signup", json=signup_data), range(2)))
    assert sorted(response.status_code for response in responses) == [201, 409]
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_persistence_across_app_instances(database_engine, signup_data):
    with TestClient(create_app(database_engine)) as first:
        assert first.post("/user/signup", json=signup_data).status_code == 201
    with TestClient(create_app(database_engine)) as second:
        assert second.post("/user/login", json=signup_data).status_code == 200


def test_password_salts_and_verification():
    password = "한글 비밀번호 🔐"
    first, second = hash_password(password), hash_password(password)
    assert first != second
    assert verify_password(password, first)
    assert verify_password(password, second)
    assert not verify_password("wrong", first)


@pytest.mark.parametrize("stored", ["plaintext", "", "pbkdf2_sha256$bad$salt$hash", "other$600000$salt$hash"])
def test_invalid_stored_hash_is_rejected(stored):
    assert not verify_password("password", stored)


def test_existing_board_routes(client):
    response = client.post("/board/register", json={"title": "제목", "contents": "내용"})
    assert response.status_code == 200
    assert client.get(f"/board/read/{response.json()['idx']}").json() == response.json()
