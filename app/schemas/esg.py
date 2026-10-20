from pydantic import BaseModel


class EsgReportDetailResponseEnvelope(BaseModel):
    code: int
    message: str
    result: "EsgReportDetailResponse"


class EsgHeadquarters(BaseModel):
    label: str
    latitude: float
    longitude: float


class EsgSources(BaseModel):
    ranking: str
    ranking_crosscheck: str
    headquarters: str
    esg_highlights: str
    ranking_verification_date: str
    headquarters_verification_date: str
    esg_highlights_verification_date: str


class EsgReportResponse(BaseModel):
    id: int
    title: str
    report_year: int
    cover_image_url: str | None
    landing_page_url: str
    source_url: str
    verification_date: str


class EsgReportDetailResponse(BaseModel):
    id: int
    company_id: str
    company_name: str
    title: str
    report_year: int
    summary: str
    page_count: int | None
    price_krw: int | None
    cover_image_url: str | None
    landing_page_url: str
    source_url: str
    verification_date: str
    purchased: bool = False
    access_url: str | None = None


class EsgCompanyResponse(BaseModel):
    company_id: str
    name: str
    rank: int
    revenue_krw: int
    industry: str
    headquarters: EsgHeadquarters
    esg_highlights: str
    sources: EsgSources
    reports: list[EsgReportResponse]


class EsgCompanyListResult(BaseModel):
    fiscal_year: int
    revenue_basis: str
    ranking_source_url: str
    companies: list[EsgCompanyResponse]


class EsgCompanyListResponse(BaseModel):
    code: int
    message: str
    result: EsgCompanyListResult
