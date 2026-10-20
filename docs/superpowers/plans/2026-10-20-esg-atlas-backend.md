# ESG Atlas Backend Implementation Plan

> **For agentic workers:** Follow the backend-dev worktree instructions and use test-driven development. Keep changes within `app/` and backend tests unless shared project configuration is required.

**Goal:** Serve a source-backed, 2025 standalone-revenue top ten company dataset and official ESG report metadata from SQLite through a public FastAPI endpoint.

**Architecture:** Store company, ranking provenance, headquarters, ESG highlight, and official report links as relational records. Seed the curated dataset idempotently at application startup and expose a read-only endpoint using the project's `{code, message, result}` response convention.

**Tech Stack:** FastAPI, SQLAlchemy 2, SQLite, Pydantic, pytest.

**Spec:** `docs/superpowers/specs/2026-10-20-korean-esg-disclosure-atlas-design.md`

## Global Constraints

- Use fiscal year 2025 and standalone (별도) revenue for the top ten listed Korean companies.
- Store revenue as integer KRW and include the source URL and verification date for ranking, headquarters, ESG highlights, and reports.
- Use public data from web research; do not scrape the web at runtime.
- Keep current user and board behavior unchanged.
- PDF and cover image URLs must point to official company sources; do not copy PDFs to the server.
- Run the complete pytest suite before marking backend work complete.

## Shared API Contract

`GET /esg/companies?fiscal_year=2025`

```json
{
  "code": 200,
  "message": "ESG 기업 목록을 조회했습니다.",
  "result": {
    "fiscal_year": 2025,
    "revenue_basis": "standalone",
    "ranking_source_url": "https://...",
    "companies": [
      {
        "company_id": "stable-slug",
        "name": "Company name",
        "rank": 1,
        "revenue_krw": 123000000000,
        "industry": "Industry",
        "headquarters": {"label": "City/district", "latitude": 37.5, "longitude": 127.0},
        "esg_highlights": "Report-based factual summary.",
        "sources": {
          "ranking": "https://...",
          "headquarters": "https://...",
          "esg_highlights": "https://..."
        },
        "reports": [
          {
            "title": "2025 Sustainability Report",
            "report_year": 2025,
            "cover_image_url": "https://...",
            "pdf_url": "https://...pdf",
            "landing_page_url": "https://...",
            "source_url": "https://..."
          }
        ]
      }
    ]
  }
}
```

The endpoint returns HTTP 200 only for the supported fiscal year 2025. Other years return 404 in the same standard error envelope. A successful list contains exactly ten companies ordered by unique ranks 1 through 10. `headquarters.latitude` and `longitude` are numeric WGS84 coordinates.

## Review Focus

- Duplicate, missing, or out-of-range ranks: assert ten companies with unique contiguous ranks.
- Invalid and unsupported fiscal years: assert validation/error behavior and standard envelope.
- Missing company sources or report links: assert data validation rejects incomplete curated records.
- Repeated application startup: assert seed is idempotent and does not duplicate rows.
- Existing authentication and board routes: run the full suite to detect regressions.

## Files

- Create `app/models/esg_company.py` for company/ranking/headquarters/provenance records.
- Create `app/models/esg_report.py` for official report metadata related to a company.
- Create `app/schemas/esg.py` for response models.
- Create `app/api/routers/esg.py` for the public list endpoint.
- Create `app/data/esg_companies_2025.json` for researched, cited seed records.
- Create `app/services/esg_seed.py` for validated, idempotent seed loading.
- Modify `app/main.py` to register models/router and seed during lifespan.
- Create `tests/test_esg_api.py` for endpoint, data integrity, and seed behavior.

## Task 1: Define models and source-backed seed data

**Interfaces:** Produces SQLAlchemy `EsgCompany` and `EsgReport` records and validated JSON records consumed by the seed service. Company identity uses `company_id`; revenue uses integer KRW; headquarters uses WGS84 latitude/longitude; sources are separate ranking, headquarters, ESG, and report URLs.

- [ ] Research the 2025 standalone top ten list using browser search and verify each revenue against company annual filings (DART/KIND); record direct source URLs and verification dates in each record.
- [ ] Find the official company headquarters location, latest relevant official ESG report, cover image or usable official cover source, PDF, and report landing page for each company; record direct URLs.
- [ ] Create `tests/test_esg_api.py` seed-data integrity tests asserting ten records, exact unique ranks 1–10, non-empty sources, positive integer revenues, valid coordinates, and official report URLs.
- [ ] Run `pytest tests/test_esg_api.py -q` and confirm the new integrity test fails before implementation.
- [ ] Implement SQLAlchemy models, JSON dataset validation, and `seed_esg_data(session)` as an idempotent insert/update keyed by stable company ID and report year.
- [ ] Run `pytest tests/test_esg_api.py -q` and confirm the integrity test passes.

## Task 2: Add the public list API

**Consumes:** Task 1 models and seed service.
**Produces:** `GET /esg/companies?fiscal_year=2025` with the shared response contract above.

- [ ] Add tests for the success envelope, ordered company fields, nested source/report fields, unsupported year 404, and stable response serialization.
- [ ] Run the focused tests and confirm failure before implementation.
- [ ] Add Pydantic response schemas and an ESG router that queries ordered companies and associated reports.
- [ ] Register ESG model imports and the router in `app/main.py`; call the idempotent seeder during lifespan after schema creation.
- [ ] Run `pytest tests/test_esg_api.py -q` and confirm all ESG API tests pass.
- [ ] Run `pytest -q` and confirm all backend tests pass.

## Task 3: Commit backend work

- [ ] Review `git diff` to ensure backend scope and source URLs are complete.
- [ ] Commit changes on the backend worktree branch with message `feat: add ESG atlas company API`.

