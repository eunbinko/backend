from pydantic import BaseModel, ConfigDict


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
    model_config = ConfigDict(from_attributes=True)
    title: str
    report_year: int
    cover_image_url: str | None
    pdf_url: str | None
    landing_page_url: str
    source_url: str
    verification_date: str


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
