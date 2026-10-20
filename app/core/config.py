import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    SECRET_KEY: str = secrets.token_urlsafe(48)
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite:///db.sqlite"
    COOKIE_SECURE: bool = False
    KAKAO_REST_API_KEY: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    KAKAO_REDIRECT_URI: str = "http://localhost:8000/user/kakao/callback"
    FRONTEND_URL: str = "http://localhost:5173"
    FRONTEND_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    KAKAO_STATE_TTL_SECONDS: int = 300


settings = Settings()
