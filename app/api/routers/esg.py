from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models.esg_company import EsgCompany
from app.models.esg_report import EsgReport
from app.models.report_order import ReportOrder
from app.schemas.esg import EsgCompanyListResponse, EsgReportDetailResponse, EsgReportDetailResponseEnvelope
from app.services.esg_pricing import calculate_report_price
import jwt
from app.core.config import settings


router = APIRouter(prefix="/esg", tags=["ESG Atlas"])


@router.get("/reports/{report_id}", response_model=EsgReportDetailResponseEnvelope)
def get_esg_report(report_id: int, request: Request, db: Session = Depends(get_db)):
    report = db.scalar(select(EsgReport).options(selectinload(EsgReport.company)).where(EsgReport.id == report_id))
    if report is None:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    purchased = False
    token = request.cookies.get("EN_AT")
    if token:
        try:
            claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(claims["sub"])
            purchased = db.scalar(select(ReportOrder.id).where(
                ReportOrder.user_id == user_id, ReportOrder.report_id == report.id,
                ReportOrder.status == "PAID",
            )) is not None
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            purchased = False
    access_url = (report.pdf_url or report.landing_page_url) if purchased else None
    return {"code": 200, "message": "보고서 상세를 조회했습니다.", "result": {
        "id": report.id, "company_id": report.company_id, "company_name": report.company.name,
        "title": report.title, "report_year": report.report_year,
        "summary": report.company.esg_highlights, "page_count": report.page_count,
        "price_krw": calculate_report_price(report.page_count), "cover_image_url": report.cover_image_url,
        "landing_page_url": report.landing_page_url, "source_url": report.source_url,
        "verification_date": report.verification_date, "purchased": purchased, "access_url": access_url,
    }}


@router.get("/companies", response_model=EsgCompanyListResponse)
def list_esg_companies(fiscal_year: int = Query(2025), db: Session = Depends(get_db)):
    if fiscal_year != 2025:
        raise HTTPException(status_code=404, detail="2025 회계연도 자료만 제공합니다.")
    companies = db.scalars(
        select(EsgCompany).options(selectinload(EsgCompany.reports))
        .where(EsgCompany.fiscal_year == fiscal_year).order_by(EsgCompany.rank)
    ).all()
    source_url = companies[0].ranking_source_url if companies else "https://v.daum.net/v/20260406110202650"
    return {
        "code": 200,
        "message": "ESG 기업 목록을 조회했습니다.",
        "result": {
            "fiscal_year": fiscal_year,
            "revenue_basis": "standalone",
            "ranking_source_url": source_url,
            "companies": [{
                "company_id": company.company_id,
                "name": company.name,
                "rank": company.rank,
                "revenue_krw": company.revenue_krw,
                "industry": company.industry,
                "headquarters": {
                    "label": company.headquarters_label,
                    "latitude": company.latitude,
                    "longitude": company.longitude,
                },
                "esg_highlights": company.esg_highlights,
                "sources": {
                    "ranking": company.ranking_source_url,
                    "ranking_crosscheck": company.ranking_crosscheck_url,
                    "headquarters": company.headquarters_source_url,
                    "esg_highlights": company.esg_source_url,
                    "ranking_verification_date": company.ranking_verification_date,
                    "headquarters_verification_date": company.headquarters_verification_date,
                    "esg_highlights_verification_date": company.esg_verification_date,
                },
                "reports": [{
                    "id": report.id, "title": report.title, "report_year": report.report_year,
                    "cover_image_url": report.cover_image_url, "landing_page_url": report.landing_page_url,
                    "source_url": report.source_url, "verification_date": report.verification_date,
                } for report in sorted(company.reports, key=lambda report: report.report_year, reverse=True)],
            } for company in companies],
        },
    }
