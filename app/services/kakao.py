import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.oauth_account import OAuthAccount
from app.models.user import User

STATE_COOKIE = "kakao_state"


@dataclass(frozen=True)
class KakaoProfile:
    provider_user_id: str
    nickname: str


class KakaoOAuthClient:
    def __init__(self):
        self.client_id = settings.KAKAO_REST_API_KEY

    def exchange_code(self, code: str) -> str:
        if not self.client_id:
            raise RuntimeError("Kakao REST API key is not configured")
        form_data = {"grant_type": "authorization_code", "client_id": self.client_id,
                     "redirect_uri": settings.KAKAO_REDIRECT_URI, "code": code}
        if settings.KAKAO_CLIENT_SECRET:
            form_data["client_secret"] = settings.KAKAO_CLIENT_SECRET
        response = httpx.post(
            "https://kauth.kakao.com/oauth/token",
            data=form_data,
            timeout=10.0,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise ValueError("Kakao token response is invalid")
        return token

    def get_profile(self, access_token: str) -> KakaoProfile:
        response = httpx.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}, timeout=10.0,
        )
        response.raise_for_status()
        return self.parse_profile(response.json())

    @staticmethod
    def parse_profile(payload: dict) -> KakaoProfile:
        kakao_id = payload.get("id")
        account = payload.get("kakao_account") or {}
        profile = account.get("profile") or {}
        nickname = profile.get("nickname") or (payload.get("properties") or {}).get("nickname")
        if isinstance(kakao_id, bool) or not isinstance(kakao_id, (str, int)) or not str(kakao_id):
            raise ValueError("Kakao profile has no valid service user ID")
        if not isinstance(nickname, str) or not nickname.strip() or len(nickname.strip()) > 100:
            raise ValueError("Kakao profile has no valid nickname")
        return KakaoProfile(str(kakao_id), nickname.strip())


def create_state() -> str:
    return secrets.token_urlsafe(32)


def sign_state(state: str) -> str:
    timestamp = str(int(time.time()))
    value = base64.urlsafe_b64encode(state.encode()).decode().rstrip("=")
    signed = f"{value}.{timestamp}"
    signature = hmac.new(settings.SECRET_KEY.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"{signed}.{signature}"


def validate_state(cookie: str | None, state: str | None) -> bool:
    if not cookie or not state:
        return False
    try:
        value, timestamp, signature = cookie.rsplit(".", 2)
        signed = f"{value}.{timestamp}"
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode(), signed.encode(), hashlib.sha256
        ).hexdigest()
        age = int(time.time()) - int(timestamp)
        expected = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode()
    except (ValueError, UnicodeDecodeError):
        return False
    return (
        age >= 0 and age <= settings.KAKAO_STATE_TTL_SECONDS
        and hmac.compare_digest(signature, expected_signature)
        and hmac.compare_digest(expected, state)
    )


def get_or_create_kakao_user(db: Session, profile: KakaoProfile) -> User:
    identity = db.scalar(select(OAuthAccount).where(
        OAuthAccount.provider == "kakao", OAuthAccount.provider_user_id == profile.provider_user_id
    ))
    if identity:
        return db.get(User, identity.user_id)

    user = User(email=None, password=hash_password(secrets.token_urlsafe(48)), name=profile.nickname)
    db.add(user)
    try:
        db.flush()
        db.add(OAuthAccount(user_id=user.idx, provider="kakao", provider_user_id=profile.provider_user_id))
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        winner = db.scalar(select(OAuthAccount).where(
            OAuthAccount.provider == "kakao", OAuthAccount.provider_user_id == profile.provider_user_id
        ))
        if winner:
            return db.get(User, winner.user_id)
        raise
