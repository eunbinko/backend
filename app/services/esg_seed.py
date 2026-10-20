from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.esg_companies_2025 import load_company_records
from app.models.esg_company import EsgCompany
from app.models.esg_report import EsgReport


def seed_esg_data(session: Session) -> None:
    for record in load_company_records():
        sources = record["sources"]
        headquarters = record["headquarters"]
        company = session.get(EsgCompany, record["company_id"])
        values = {
            "name": record["name"], "fiscal_year": 2025, "revenue_basis": "standalone",
            "rank": record["rank"], "revenue_krw": record["revenue_krw"], "industry": record["industry"],
            "headquarters_label": headquarters["label"], "latitude": headquarters["latitude"],
            "longitude": headquarters["longitude"], "esg_highlights": record["esg_highlights"],
            "ranking_source_url": sources["ranking"],
            "ranking_crosscheck_url": sources["ranking_crosscheck"],
            "ranking_verification_date": sources["ranking_verification_date"],
            "headquarters_source_url": sources["headquarters"],
            "headquarters_verification_date": sources["headquarters_verification_date"],
            "esg_source_url": sources["esg_highlights"],
            "esg_verification_date": sources["esg_highlights_verification_date"],
        }
        if company is None:
            company = EsgCompany(company_id=record["company_id"], **values)
            session.add(company)
            session.flush()
        else:
            for key, value in values.items():
                setattr(company, key, value)
        for report_data in record["reports"]:
            report = session.scalar(select(EsgReport).where(
                EsgReport.company_id == company.company_id,
                EsgReport.report_year == report_data["report_year"],
            ))
            report_values = {
                "title": report_data["title"], "cover_image_url": report_data.get("cover_image_url"),
                "pdf_url": report_data["pdf_url"], "landing_page_url": report_data["landing_page_url"],
                "source_url": report_data["source_url"], "verification_date": report_data["verification_date"],
            }
            if report is None:
                session.add(EsgReport(company_id=company.company_id, report_year=report_data["report_year"], **report_values))
            else:
                for key, value in report_values.items():
                    setattr(report, key, value)
    session.commit()
