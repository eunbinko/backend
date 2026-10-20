import pytest

from app.data.esg_companies_2025 import load_company_records, validate_company_records
from app.services.esg_seed import seed_esg_data


def test_curated_dataset_has_ten_complete_ordered_companies():
    records = load_company_records()
    validate_company_records(records)
    assert len(records) == 10
    assert [record["rank"] for record in records] == list(range(1, 11))
    for record in records:
        assert isinstance(record["revenue_krw"], int) and record["revenue_krw"] > 0
        assert all(record["sources"].get(key, "").startswith("https://") for key in ("ranking", "headquarters", "esg_highlights"))
        assert record["sources"]["ranking_crosscheck"].startswith("https://")
        assert record["headquarters"]["label"]
        assert -90 <= record["headquarters"]["latitude"] <= 90
        assert -180 <= record["headquarters"]["longitude"] <= 180
        assert record["reports"], record["company_id"]
        for report in record["reports"]:
            assert report["landing_page_url"].startswith("https://")
            assert report["source_url"].startswith("https://")
            if report.get("pdf_url"):
                assert report["pdf_url"].startswith("https://")
            if report.get("cover_image_url"):
                assert report["cover_image_url"].startswith("https://")


def test_invalid_dataset_rank_is_rejected():
    records = load_company_records()
    records[0]["rank"] = 11
    with pytest.raises(ValueError):
        validate_company_records(records)


def test_esg_endpoint_returns_source_backed_ranked_companies(client):
    response = client.get("/esg/companies?fiscal_year=2025")
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    result = payload["result"]
    assert result["fiscal_year"] == 2025
    assert result["revenue_basis"] == "standalone"
    companies = result["companies"]
    assert len(companies) == 10
    assert [company["rank"] for company in companies] == list(range(1, 11))
    first = companies[0]
    assert first["company_id"] and first["revenue_krw"] > 0
    assert first["sources"]["ranking_verification_date"] == "2026-10-20"
    assert first["sources"]["ranking_crosscheck"].startswith("https://")
    assert first["headquarters"]["latitude"]
    assert first["reports"][0]["pdf_url"].startswith("https://")


def test_unsupported_fiscal_year_uses_standard_error_envelope(client):
    response = client.get("/esg/companies?fiscal_year=2024")
    assert response.status_code == 404
    assert response.json() == {
        "code": 404,
        "message": "2025 회계연도 자료만 제공합니다.",
        "result": None,
    }


def test_repeated_seed_is_idempotent(database_engine):
    from sqlalchemy.orm import Session
    from app.db.database import Base
    from app.models.esg_company import EsgCompany
    from app.models.esg_report import EsgReport

    Base.metadata.create_all(database_engine)
    with Session(database_engine) as session:
        seed_esg_data(session)
        seed_esg_data(session)
        assert session.query(EsgCompany).count() == 10
        assert session.query(EsgReport).count() == 10


