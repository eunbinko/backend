from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from fastapi import APIRouter, Depends, HTTPException

from app.models.board import Board
from app.schemas.board import BoardListRes, BoardRes, RegisterReq, RegisterRes

router = APIRouter(prefix="/board", tags=["board"])


@router.post("/register", response_model=RegisterRes)
def register(req: RegisterReq, db: Session = Depends(get_db)):
    board = Board(
        title=req.title, contents=req.contents
    )
    db.add(board)
    db.commit()
    db.refresh(board)
    return {"code": 200, "message": "게시글이 등록되었습니다.", "result": board}


@router.get("", response_model=BoardListRes)
def list_boards(db: Session = Depends(get_db)):
    boards = db.scalars(select(Board).order_by(Board.idx.desc())).all()
    return {"code": 200, "message": "게시글 목록을 조회했습니다.", "result": boards}


@router.get("/read/{idx}", response_model=BoardRes)
def read(idx: int, db: Session = Depends(get_db)):
    board = db.get(Board, idx)
    if board is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return {"code": 200, "message": "게시글을 조회했습니다.", "result": board}













