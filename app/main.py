from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException

from app.api.routers import board, esg, report_purchase, user
from app.core.config import settings
from app.db.database import Base, engine, get_db
from app.models.user import User
from app.models.oauth_account import OAuthAccount  # noqa: F401
from app.db.migrations import migrate_sqlite_esg_report_page_count, migrate_sqlite_user_email_nullable
from app.models.esg_company import EsgCompany  # noqa: F401
from app.models.esg_report import EsgReport  # noqa: F401
from app.models.report_order import ReportOrder  # noqa: F401
from app.services.esg_seed import seed_esg_data


def create_app(database_engine=engine):
    @asynccontextmanager
    async def lifespan(application):
        migrate_sqlite_user_email_nullable(database_engine)
        migrate_sqlite_esg_report_page_count(database_engine)
        Base.metadata.create_all(bind=database_engine)
        # create_all does not add indexes to an existing table.
        for index in User.__table__.indexes:
            index.create(bind=database_engine, checkfirst=True)
        with sessionmaker(bind=database_engine, autoflush=False)() as session:
            seed_esg_data(session)
        yield

    application = FastAPI(title="회원 API", version="0.1.0", lifespan=lifespan)
    sessions = sessionmaker(bind=database_engine, autoflush=False)

    def session_dependency():
        with sessions() as session:
            yield session

    application.dependency_overrides[get_db] = session_dependency
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",") if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(user.router)
    application.include_router(board.router)
    application.include_router(esg.router)
    application.include_router(report_purchase.router)

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code,
                            content={"code": exc.status_code, "message": str(exc.detail), "result": None},
                            headers=exc.headers)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Do not reflect passwords from invalid request bodies.
        return JSONResponse(status_code=422,
                            content={"code": 422, "message": "요청값이 올바르지 않습니다.",
                                     "result": "입력값을 확인해 주세요."})

    @application.get("/")
    def main():
        return {"code": 200, "message": "메인 페이지입니다.", "result": None}

    return application


app = create_app()
