# 전체 서버 진입점, FastAPI 객체 생성, 라우터 등록, 테이블 생성

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routers import user, board
from app.db.database import Base, engine
from app.models.board import Board
from app.models.user import User
app = FastAPI(title="노트 API", version="0.1.0")

app.include_router(user.router)
app.include_router(board.router)

Base.metadata.create_all(bind=engine)

@app.get("/")
def main():
    return {"message": "메인 페이지입니다."}


# 순수 HTML/CSS/JS 노트 웹 페이지
app.mount("/web", StaticFiles(directory=Path(__file__).resolve().parent / "web", html=True), name="web")
