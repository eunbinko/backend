import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from app.core.config import settings

ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(rounds) != ITERATIONS:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds))
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def createToken(userId: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": userId, "iat": now, "exp": now + timedelta(minutes=30)},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
