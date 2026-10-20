from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models.esg_company import EsgCompany
from app.schemas.esg import EsgCompanyListResponse


router = APIRouter(prefix="/esg", tags=["ESG Atlas"])


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
                "reports": sorted(company.reports, key=lambda report: report.report_year, reverse=True),
            } for company in companies],
        },
    }
