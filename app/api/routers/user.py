from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import createToken, hash_password, verify_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import LoginReq, LoginRes, SignUpReq, SignUpRes

router = APIRouter(prefix="/user", tags=["user"])
_DUMMY_HASH = hash_password("dummy-password-for-timing")


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
    res.set_cookie(
        "EN_AT", createToken(user.email), httponly=True,
        secure=settings.COOKIE_SECURE, samesite="lax", max_age=1800,
    )
    return {"code": 200, "message": "로그인에 성공했습니다.", "result": user}
