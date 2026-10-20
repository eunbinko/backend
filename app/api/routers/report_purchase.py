import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.services.portone import (
    PortOneConfigurationError, complete_pending_order, create_pending_order,
)


router = APIRouter(prefix="/esg", tags=["ESG Report Purchase"])


def authenticated_user(request: Request, db: Session) -> User:
    token = request.cookies.get("EN_AT")
    if not token:
        raise HTTPException(401, "로그인이 필요합니다.")
    try:
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(401, "로그인이 필요합니다.") from None
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(401, "로그인이 필요합니다.")
    return user


@router.post("/reports/{report_id}/orders")
def create_report_order(report_id: int, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    try:
        result = create_pending_order(db, user.idx, report_id)
    except PortOneConfigurationError as error:
        raise HTTPException(503, str(error)) from None
    except LookupError as error:
        raise HTTPException(404, str(error)) from None
    except (ValueError, FileExistsError) as error:
        raise HTTPException(409, str(error)) from None
    return {"code": 200, "message": "결제 주문을 준비했습니다.", "result": result}


@router.post("/orders/{payment_id}/complete")
def complete_report_order(payment_id: str, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    try:
        result = complete_pending_order(db, user.idx, payment_id)
    except PortOneConfigurationError as error:
        raise HTTPException(503, str(error)) from None
    except LookupError as error:
        raise HTTPException(404, str(error)) from None
    except ValueError as error:
        raise HTTPException(409, str(error)) from None
    return {"code": 200, "message": "결제를 확인했습니다.", "result": result}
