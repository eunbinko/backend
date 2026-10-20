import json
from pathlib import Path
from urllib.parse import urlparse


DATA_PATH = Path(__file__).with_name("esg_companies_2025.json")


def load_company_records() -> list[dict]:
    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    validate_company_records(records)
    return records


def _is_https_url(value: object) -> bool:
    return isinstance(value, str) and urlparse(value).scheme == "https" and bool(urlparse(value).netloc)


def validate_company_records(records: list[dict]) -> None:
    if len(records) != 10 or sorted(row.get("rank", 0) for row in records) != list(range(1, 11)):
        raise ValueError("2025년 기업 레코드는 순위 1~10의 10개여야 합니다.")
    ids = [row.get("company_id") for row in records]
    if len(set(ids)) != 10 or not all(ids):
        raise ValueError("기업 식별자는 중복될 수 없고 필수입니다.")
    for row in records:
        hq = row.get("headquarters", {})
        sources = row.get("sources", {})
        if (not row.get("name") or not isinstance(row.get("revenue_krw"), int) or row["revenue_krw"] <= 0
                or not hq.get("label") or not isinstance(hq.get("latitude"), (int, float))
                or not isinstance(hq.get("longitude"), (int, float))
                or not -90 <= hq["latitude"] <= 90 or not -180 <= hq["longitude"] <= 180):
            raise ValueError(f"기업 레코드 필드가 유효하지 않습니다: {row.get('company_id')}")
        if not _is_https_url(sources.get("ranking_crosscheck")):
            raise ValueError(f"순위 교차확인 출처 URL이 필요합니다: {row.get('company_id')}")
        for source_name in ("ranking", "headquarters", "esg_highlights"):
            if not _is_https_url(sources.get(source_name)) or not sources.get(f"{source_name}_verification_date"):
                raise ValueError(f"출처 URL과 확인일이 필요합니다: {row.get('company_id')} / {source_name}")
        if not row.get("esg_highlights") or not isinstance(row.get("reports", []), list) or not row.get("reports"):
            raise ValueError(f"기업별 공식 보고서 정보가 필요합니다: {row.get('company_id')}")
        for report in row.get("reports", []):
            required = ("landing_page_url", "source_url")
            if (not report.get("title") or not isinstance(report.get("report_year"), int)
                    or any(not _is_https_url(report.get(key)) for key in required)
                    or not report.get("verification_date")):
                raise ValueError(f"보고서 필드가 유효하지 않습니다: {row.get('company_id')}")
            if report.get("pdf_url") is not None and not _is_https_url(report["pdf_url"]):
                raise ValueError(f"PDF URL이 유효하지 않습니다: {row.get('company_id')}")
            if report.get("cover_image_url") is not None and not _is_https_url(report["cover_image_url"]):
                raise ValueError(f"표지 이미지 URL이 유효하지 않습니다: {row.get('company_id')}")


