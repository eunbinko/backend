from sqlalchemy.orm import Session
from app.db.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.models.board import Board
from app.schemas.board import RegisterReq, RegisterRes, ReadRes

router = APIRouter(prefix="/board", tags=["board"])


@router.post("/register", response_model=RegisterRes)
def register(req: RegisterReq, db: Session = Depends(get_db)):
    board = Board(
        title=req.title, contents=req.contents
    )
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


@router.get("/read/{idx}", response_model=ReadRes)
def read(idx: int, db: Session = Depends(get_db)):
    board = db.get(Board, idx)
    return board













