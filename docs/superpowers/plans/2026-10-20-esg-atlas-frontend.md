# ESG Atlas Frontend Implementation Plan

> **For agentic workers:** Follow the frontend-dev worktree instructions and use test-driven development. Keep changes within `frontend/` unless shared project configuration is required.

**Goal:** Replace the public Vue homepage with an accessible ESG disclosure atlas showing ten company locations, report-cover threads, company facts, and an official-source PDF overlay.

**Architecture:** Fetch the backend's source-backed company list through an Axios API module. Render it in a responsive map-centered layout with a Korea map, company markers, SVG thread overlays, side report-cover lists, and a PDF dialog that always provides an official-source fallback link.

**Tech Stack:** Vue 3, Axios, Leaflet, Jest, jsdom, CSS/SVG.

**Spec:** `docs/superpowers/specs/2026-10-20-korean-esg-disclosure-atlas-design.md`

## Global Constraints

- Use `GET /esg/companies?fiscal_year=2025` and the shared response contract in `2026-10-20-esg-atlas-backend.md`.
- Do not hard-code company ranking/data in Vue; render the backend response and its sources.
- Keep the initial public atlas usable without login.
- Use official cover/PDF URLs and do not add payment or PDF storage flows.
- Provide map tile attribution and an official PDF link even while the PDF is embedded.
- Run the complete Jest suite and frontend build before marking frontend work complete.

## Shared API Contract

The frontend consumes `GET /esg/companies?fiscal_year=2025`. The response envelope is `{code, message, result}`; `result` carries `fiscal_year`, `revenue_basis`, `ranking_source_url`, and `companies`. Each company has `company_id`, `name`, `rank`, `revenue_krw`, `industry`, `headquarters {label, latitude, longitude}`, `esg_highlights`, `sources {ranking, headquarters, esg_highlights}`, and `reports[]` with `title`, `report_year`, `cover_image_url`, `pdf_url`, `landing_page_url`, `source_url`. The backend plan is the source of truth for the full example.

## Review Focus

- API delay/failure/empty result: show understandable loading, retry, and empty states.
- Cover image failure: preserve the card title and offer the report landing page link.
- Cross-origin PDF viewer restrictions: always show an official PDF link in the dialog.
- Keyboard selection and dialog close: use buttons, accessible labels, focus visibility, Escape close, and restore focus.
- Narrow viewport and reduced-motion preference: retain map/selection clarity without off-screen controls or required animation.

## Files

- Create `frontend/src/api/esg.js` for Axios data retrieval and envelope/error handling.
- Create `frontend/src/components/KoreaCompanyMap.vue` for map tiles and selectable markers.
- Create `frontend/src/components/ReportCoverRail.vue` for side cover cards and image fallback.
- Create `frontend/src/components/ReportPdfDialog.vue` for the accessible PDF overlay.
- Create `frontend/src/components/AtlasThreads.vue` for responsive SVG links between map points and cards.
- Create `frontend/src/views/EsgAtlasView.vue` for page state, selection, provenance, and component composition.
- Modify `frontend/src/App.vue` to make the atlas the public home view while leaving auth API behavior intact.
- Modify `frontend/src/style.css` for the approved atlas visual system and responsive/accessibility behavior.
- Modify `frontend/package.json` and lockfile to add Axios and Leaflet if not already available.
- Create Jest tests next to API/view components for fetch, interaction, and error states.

## Task 1: Add the API module and atlas view state

**Interfaces:** `fetchEsgCompanies({ fiscalYear: 2025 })` resolves to `result` from the standard envelope or throws a user-displayable error. The view state owns `companies`, `selectedCompanyId`, `loading`, and `error`.

- [ ] Add Jest tests for unwrapping the success response, request URL and year, non-2xx response, malformed response, and retry behavior.
- [ ] Run the focused Jest test and confirm it fails before implementation.
- [ ] Add Axios if needed and implement `frontend/src/api/esg.js`; create `EsgAtlasView.vue` data-loading and selection state.
- [ ] Run the focused Jest test and confirm it passes.

## Task 2: Build map and report-cover rails

**Consumes:** Task 1 company list and selected company ID.
**Produces:** Selectable map marker anchors keyed by `company_id` and cover-card anchors keyed by `company_id`/report year.

- [ ] Test that company records render markers and corresponding cover cards, and selecting either updates the selected company.
- [ ] Run the focused Jest test and confirm it fails before implementation.
- [ ] Implement `KoreaCompanyMap.vue` using Leaflet with OpenStreetMap tile attribution; markers use backend WGS84 coordinates.
- [ ] Implement `ReportCoverRail.vue` with image fallback and company/report labels.
- [ ] Run focused Jest tests and confirm marker/cover rendering and selection pass.

## Task 3: Connect threads and add report PDF dialog

**Consumes:** Task 2 marker/card identities and report metadata.
**Produces:** SVG thread overlay for the selected company and an accessible PDF dialog with an official-source link.

- [ ] Test selected-company thread state, opening the matching PDF, Escape close, explicit close, focus restoration, and permanent official URL fallback.
- [ ] Run focused Jest tests and confirm they fail before implementation.
- [ ] Implement `AtlasThreads.vue` and `ReportPdfDialog.vue`; use keyboard-operable controls and avoid relying on cross-origin iframe load detection.
- [ ] Run focused Jest tests and confirm connection and PDF interactions pass.

## Task 4: Integrate the atlas homepage and responsive styling

- [ ] Test that `App.vue` displays the atlas on the public route and does not eagerly call existing board/auth endpoints.
- [ ] Run the focused Jest test and confirm it fails before implementation.
- [ ] Integrate `EsgAtlasView.vue` at the public route and preserve signup/login routes and API behavior.
- [ ] Add the approved blue-grey atlas, report-cover rail, thread emphasis, focus treatment, narrow-layout transformation, reduced-motion handling, and map attribution styling.
- [ ] Run `npm test -- --runInBand` and confirm the full Jest suite passes.
- [ ] Run `npm run build` and confirm the production build succeeds.

## Task 5: Commit frontend work

- [ ] Review `git diff` for scope, attribution, and official URL fallbacks.
- [ ] Commit changes on the frontend worktree branch with message `feat: build ESG disclosure atlas frontend`.

