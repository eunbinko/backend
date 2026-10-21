from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import createToken, hash_password, verify_password
from app.db.database import get_db
from app.models.user import User
from app.services.kakao import KakaoOAuthClient, STATE_COOKIE, create_state, get_or_create_kakao_user, sign_state, validate_state
from app.schemas.user import LoginReq, LoginRes, SignUpReq, SignUpRes

router = APIRouter(prefix="/user", tags=["user"])
_DUMMY_HASH = hash_password("dummy-password-for-timing")
_KAKAO_CALLBACK_PATH = "/user/kakao/callback"


def set_login_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        "EN_AT", createToken(str(user.idx)), httponly=True,
        secure=settings.COOKIE_SECURE, samesite="lax", max_age=1800,
        domain=settings.COOKIE_DOMAIN,
    )


@router.post("/signup", response_model=SignUpRes, status_code=201)
def signup(req: SignUpReq, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == req.email)):
        raise HTTPException(409, "이미 가입한 이메일입니다.")
    user = User(email=req.email, password=hash_password(req.password), name=req.name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(User).where(User.email == req.email)):
            raise HTTPException(409, "이미 가입한 이메일입니다.") from None
        raise
    db.refresh(user)
    return {"code": 201, "message": "회원가입이 완료되었습니다.", "result": user}


@router.post("/login", response_model=LoginRes)
def login(req: LoginReq, res: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == req.email))
    valid = verify_password(req.password, user.password if user else _DUMMY_HASH)
    if user is None or not valid:
        raise HTTPException(401, "이메일 또는 비밀번호가 올바르지 않습니다.")
    set_login_cookie(res, user)
    return {"code": 200, "message": "로그인에 성공했습니다.", "result": user}

@router.get("/me")
def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("EN_AT")
    if not token:
        return {"code": 200, "message": "로그아웃 상태", "result": None}
    try:
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return {"code": 200, "message": "로그아웃 상태", "result": None}
    user = db.get(User, user_id)
    if user is None:
        return {"code": 200, "message": "로그아웃 상태", "result": None}
    return {"code": 200, "message": "현재 로그인 사용자", "result": {"email": user.email, "name": user.name}}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        "EN_AT", httponly=True, secure=settings.COOKIE_SECURE, samesite="lax", path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    return {"code": 200, "message": "로그아웃되었습니다.", "result": None}


@router.post("/kakao/state")
def kakao_state(response: Response):
    state = create_state()
    response.set_cookie(
        STATE_COOKIE, sign_state(state), max_age=settings.KAKAO_STATE_TTL_SECONDS,
        httponly=True, secure=settings.COOKIE_SECURE, samesite="lax", path=_KAKAO_CALLBACK_PATH,
        domain=settings.COOKIE_DOMAIN,
    )
    return {"code": 200, "message": "Kakao login state created", "result": {"state": state}}


@router.get("/kakao/callback")
def kakao_callback(
    request: Request, code: str | None = None, state: str | None = None,
    error: str | None = None, db: Session = Depends(get_db),
):
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    failure = RedirectResponse(f"{frontend_url}/login?social_error=kakao", status_code=302)
    failure.delete_cookie(
        STATE_COOKIE, path=_KAKAO_CALLBACK_PATH, secure=settings.COOKIE_SECURE, samesite="lax",
        domain=settings.COOKIE_DOMAIN,
    )
    if error or not code or not validate_state(request.cookies.get(STATE_COOKIE), state):
        return failure
    try:
        client = KakaoOAuthClient()
        profile = client.get_profile(client.exchange_code(code))
        user = get_or_create_kakao_user(db, profile)
    except Exception:
        db.rollback()
        return failure

    response = RedirectResponse(f"{frontend_url}/", status_code=302)
    response.delete_cookie(
        STATE_COOKIE, path=_KAKAO_CALLBACK_PATH, secure=settings.COOKIE_SECURE, samesite="lax",
        domain=settings.COOKIE_DOMAIN,
    )
    set_login_cookie(response, user)
    return response
