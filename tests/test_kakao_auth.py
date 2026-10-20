from unittest.mock import Mock

import jwt
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import create_app
from app.models.oauth_account import OAuthAccount
from app.models.user import User
from app.services.kakao import KakaoOAuthClient, KakaoProfile


def test_state_endpoint_sets_signed_http_only_cookie(client):
    response = client.post("/user/kakao/state")
    assert response.status_code == 200
    state = response.json()["result"]["state"]
    assert len(state) >= 32
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert f"Max-Age={settings.KAKAO_STATE_TTL_SECONDS}" in cookie
    assert "Path=/user/kakao/callback" in cookie


def test_callback_rejects_invalid_state_without_provider_call(client, monkeypatch):
    exchange = Mock(side_effect=AssertionError("provider must not be called"))
    monkeypatch.setattr(KakaoOAuthClient, "exchange_code", exchange)
    signed_cookie = client.post("/user/kakao/state").cookies["kakao_state"]
    response = client.get(
        "/user/kakao/callback?code=private&state=wrong",
        headers={"Cookie": f"kakao_state={signed_cookie}"}, follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == f"{settings.FRONTEND_URL}/login?social_error=kakao"
    assert exchange.call_count == 0
    assert response.headers.get("set-cookie", "").startswith("kakao_state=")


def test_local_login_token_uses_internal_user_id(client, signup_data, database_engine):
    client.post("/user/signup", json=signup_data)
    response = client.post("/user/login", json=signup_data)
    claims = jwt.decode(response.cookies["EN_AT"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    with Session(database_engine) as db:
        user = db.scalar(select(User))
        assert claims["sub"] == str(user.idx)


def test_profile_parser_uses_only_id_and_nickname():
    client = KakaoOAuthClient()
    profile = client.parse_profile({
        "id": 123456,
        "kakao_account": {"profile": {"nickname": "Kakao Nick"}, "email": "ignored@example.com"},
    })
    assert profile == KakaoProfile(provider_user_id="123456", nickname="Kakao Nick")
    assert not hasattr(profile, "email")


def test_profile_parser_rejects_missing_id_or_nickname():
    for payload in ({"id": 123, "kakao_account": {}}, {"kakao_account": {"profile": {"nickname": "Name"}}}):
        with pytest.raises(ValueError):
            KakaoOAuthClient.parse_profile(payload)


def test_callback_creates_then_reuses_kakao_account(client, database_engine, monkeypatch):
    monkeypatch.setattr(KakaoOAuthClient, "exchange_code", lambda self, code: "test-access-token")
    monkeypatch.setattr(
        KakaoOAuthClient, "get_profile",
        lambda self, token: KakaoProfile(provider_user_id="kakao-42", nickname="Kakao Nick"),
    )
    state_response = client.post("/user/kakao/state")
    state = state_response.json()["result"]["state"]
    state_cookie = state_response.cookies["kakao_state"]
    first = client.get(
        f"/user/kakao/callback?code=code1&state={state}",
        headers={"Cookie": f"kakao_state={state_cookie}"}, follow_redirects=False,
    )
    assert first.status_code == 302 and first.headers["location"] == f"{settings.FRONTEND_URL}/"
    claims = jwt.decode(first.cookies["EN_AT"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    state2_response = client.post("/user/kakao/state")
    state2 = state2_response.json()["result"]["state"]
    second_state = state2_response.cookies["kakao_state"]
    second = client.get(
        f"/user/kakao/callback?code=code2&state={state2}",
        headers={"Cookie": f"kakao_state={second_state}"}, follow_redirects=False,
    )
    assert second.status_code == 302
    second_claims = jwt.decode(second.cookies["EN_AT"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert second_claims["sub"] == claims["sub"]
    with Session(database_engine) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
        assert db.scalar(select(func.count()).select_from(OAuthAccount)) == 1
        user = db.scalar(select(User))
        assert user.email is None and user.name == "Kakao Nick"


def test_provider_failure_redirects_without_session_or_user(client, database_engine, monkeypatch):
    monkeypatch.setattr(KakaoOAuthClient, "exchange_code", Mock(side_effect=RuntimeError("provider down")))
    state_response = client.post("/user/kakao/state")
    state = state_response.json()["result"]["state"]
    state_cookie = state_response.cookies["kakao_state"]
    response = client.get(
        f"/user/kakao/callback?code=code&state={state}",
        headers={"Cookie": f"kakao_state={state_cookie}"}, follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == f"{settings.FRONTEND_URL}/login?social_error=kakao"
    assert "EN_AT" not in response.cookies
    with Session(database_engine) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0
