from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.schemas.user import LoginReq, LoginRes, SignUpReq, SignUpRes
from app.core.security import createToken
from app.db.database import SessionLocal
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter(prefix="/user", tags=["user"])

# 제어의 역전 : IoC, 객체 생성이나 프로그램의 실행 흐름의 제어를 외부로 넘기는 프로그래밍 방식
# 의존성 주입 : DI, 필요한 객체를 우리가 직접 생성하지 않고 외부에서 전달해주는 방식
@router.post("/signup", response_model=SignUpRes)
def signup(req: SignUpReq, db: Session = Depends(get_db)):
    # db = SessionLocal()

    user = db.scalar(select(User).where(User.email == req.email))
    if user:
        print("중복 가입")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 가입된 이메일입니다.")


    newUser = User(
        email=req.email, password=req.password, name=req.name
    )
    db.add(newUser)
    db.commit()
    return req

@router.post("/login", response_model=LoginRes)
def login(req: LoginReq, res: Response):
    db = SessionLocal()
    # 회원 가입이 되어있는지 아닌지 확인
    user = db.scalar(select(User).where(User.email == req.email))
    if user:
        if user.password == req.password:
            res.set_cookie(
                "EN_AT",
                createToken(req.email),
                httponly=True,
                secure=False,
                samesite="lax"
            )
            print("정상 로그인")
            return user
    print("비정상 로그인")

    return user

