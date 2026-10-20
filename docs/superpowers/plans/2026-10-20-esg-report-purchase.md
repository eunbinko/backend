# ESG Report Purchase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add report detail pages and a verified PortOne V2 one-time purchase flow for eligible ESG reports.

**Architecture:** Integrate the existing ESG atlas commits with the committed Kakao-auth base, then add verified page-count metadata and a SQLite order/entitlement model. FastAPI creates server-priced orders and verifies them against PortOne V2; Vue requests payment through the V2 SDK and reveals the issuer's official report URL only after backend confirmation.

**Tech Stack:** Vue 3, Vite, Jest, FastAPI, SQLAlchemy 2, SQLite, pytest, PortOne Browser SDK V2, Toss Payments V2.

**Spec:** `docs/superpowers/specs/2026-10-20-esg-report-purchase-design.md`

## Global Constraints

- Use `ceil(page_count / 100) * 1000` KRW, with page counts verified from official PDF sources.
- Keep existing PortOne console settings unchanged; configure Store ID, Toss Payments V2 channel key, and API secret through environment variables.
- Keep PortOne API secrets server-side and never log or return them.
- Do not copy, download, proxy, or host issuer PDFs in this phase.
- Do not expose issuer PDF URLs to users who have not purchased the report.
- Use the logged-in user's existing HttpOnly cookie session for order ownership.
- Preserve unrelated working-tree changes and do not include them in feature commits.
- Do not use subagents; the primary agent implements and reviews all tasks.
- Run pytest, Jest, and Vite production build before claiming completion.

## Review Focus

- Missing/unverified PDF page count: purchase stays unavailable and no price is guessed (Task 2 metadata and API tests).
- Client alters report or amount after order creation: persisted server-side order and PortOne response comparison reject mismatch (Tasks 3 and 4 tests).
- Payment canceled, pending, or API unreachable: report remains unpurchased and retry is safe (Tasks 3, 4, and 6 tests).
- Duplicate completion or duplicate purchase: completion is idempotent and only one user/report entitlement is granted (Tasks 3 and 4 tests).
- Unauthenticated user or another user's payment ID: order endpoints reject access and no report URL is returned (Task 4 authorization tests).

---

### Task 1: Prepare an isolated integration worktree with the existing ESG atlas

**Files:**
- Worktree: `.worktrees/esg-report-purchase` based on current `main` after Kakao commit `39d52cb`
- Integrate backend commit: `6b44ddb` (`work/esg-backend`)
- Integrate frontend commits: `1d4d085` and `fe9ae6a` (`work/esg-frontend`)
- Review only: root `AGENTS.md`, `frontend/src/style.css`, `frontend/index.html`, and untracked documentation/assets; do not stage or overwrite them

**Interfaces:**
- Consumes: committed Kakao authentication implementation and existing ESG branch commits.
- Produces: an isolated branch containing both ESG API and Vue atlas, with Kakao login preserved and no unrelated root worktree changes copied into the feature branch.

- [ ] **Step 1: Create the feature worktree from `39d52cb`**

Run: `git worktree add -b work/esg-report-purchase .worktrees/esg-report-purchase 39d52cb`
Expected: a clean isolated worktree on `work/esg-report-purchase`.

- [ ] **Step 2: Integrate the committed ESG backend and frontend changes**

Merge `6b44ddb` and `fe9ae6a` into the feature branch in separate operations. Resolve any `App.vue` overlap by preserving Kakao login and ESG routing. Do not merge uncommitted auth overlays from either old worktree.

- [ ] **Step 3: Verify the integration base**

Run: `git status --short --branch` in the feature worktree.
Expected: clean branch containing both ESG commits and Kakao login, with no root-only design/documentation artifacts.

### Task 2: Add verified report page counts and detail metadata

**Files:**
- Modify: `app/data/esg_companies_2025.json`
- Modify: `app/models/esg_report.py`
- Modify: `app/db/migrations.py`
- Modify: `app/services/esg_seed.py`
- Modify: `app/schemas/esg.py`
- Modify: `app/api/routers/esg.py`
- Modify: `app/main.py`
- Test: `tests/test_esg_api.py` (existing ESG API test module)

**Interfaces:**
- Consumes: current `EsgReport` seed and list response.
- Produces: nullable `page_count`; `calculate_report_price(page_count: int) -> int | None`; `migrate_sqlite_esg_report_page_count(engine) -> None`; `GET /esg/reports/{report_id}` with public metadata and optional purchase state, including a stable report ID but no unpurchased PDF URL.

- [ ] **Step 1: Record official PDF page counts where verified**

Inspect each configured official PDF or issuer-hosted report. Add the verified integer count to its report record; use `null` when there is no direct PDF or its page count cannot be verified. Do not infer counts from file size, cover image, or title.

- [ ] **Step 2: Add failing tests for pricing and detail response privacy**

Test that 1, 100, 101, and 200 pages calculate to 1,000, 1,000, 2,000, and 2,000 KRW; null/zero/negative page counts are ineligible. Assert unauthenticated detail/list responses never expose `pdf_url` or an access URL. Test that a pre-existing SQLite `esg_report` table migrates to include `page_count` without changing its existing report rows.

- [ ] **Step 3: Run focused tests and verify the expected failures**

Run: `..\..\.venv\Scripts\python.exe -m pytest tests/test_esg_api.py -q --basetemp .pytest-tmp-esg-api`
Expected: FAIL because pricing, page-count metadata, and detail response privacy do not yet exist.

- [ ] **Step 4: Implement report page-count persistence, pricing, and safe detail response**

Persist `page_count` from the seed and implement `migrate_sqlite_esg_report_page_count(engine)` as an idempotent SQLite column migration called before metadata creation; it must preserve existing report rows. Calculate the price only on the backend, and add a report-detail response that uses the existing company ESG highlights as its short summary. Remove public `pdf_url` exposure from the company list response while preserving official source attribution.

- [ ] **Step 5: Run focused ESG tests**

Run: `..\..\.venv\Scripts\python.exe -m pytest tests/test_esg_api.py -q --basetemp .pytest-tmp-esg-api`
Expected: PASS, including the five-page-count privacy/pricing cases.

### Task 3: Add PortOne order and purchase persistence

**Files:**
- Create: `app/models/report_order.py`
- Modify: `app/main.py`
- Modify: `app/core/config.py`
- Modify: `.env.example`
- Modify: `app/services/portone.py`
- Test: `tests/test_report_purchase.py`

**Interfaces:**
- Consumes: eligible `EsgReport` records and authenticated `User` IDs.
- Produces: `ReportOrder(user_id, report_id, payment_id, amount_krw, status)` with unique payment ID and a unique paid entitlement per user/report; settings `PORTONE_STORE_ID`, `PORTONE_TOSSPAYMENTS_CHANNEL_KEY`, `PORTONE_API_SECRET`; a PortOne V2 payment lookup service.

- [ ] **Step 1: Add failing model/service tests**

Test pending-order persistence, unique payment IDs, a single entitlement for one user/report, secure missing-setting errors, and mocked PortOne V2 lookup success/network failure without any live credentials.

- [ ] **Step 2: Run focused tests and verify the expected failures**

Run: `..\..\.venv\Scripts\python.exe -m pytest tests/test_report_purchase.py -q --basetemp .pytest-tmp-esg-api`
Expected: FAIL because order persistence and PortOne service do not yet exist.

- [ ] **Step 3: Implement order model and create/upgrade behavior for SQLite**

Register the model before metadata creation. `create_all` must add the new order table idempotently without rebuilding or replacing unrelated user data; report-column migration is implemented in Task 2.

- [ ] **Step 4: Implement the server-side PortOne V2 lookup service**

Use the existing `httpx` dependency to call `GET https://api.portone.io/payments/{paymentId}` with `Authorization: PortOne <secret>` and an explicit timeout. Do not include secrets in errors or logs.

- [ ] **Step 5: Run focused service/model tests**

Run: `..\..\.venv\Scripts\python.exe -m pytest tests/test_report_purchase.py -q --basetemp .pytest-tmp-esg-api`
Expected: PASS with PortOne calls mocked and no network transaction.

### Task 4: Add authenticated order, completion, and report access APIs

**Files:**
- Create: `app/api/routers/report_purchase.py`
- Modify: `app/main.py`
- Modify: `app/schemas/esg.py`
- Test: `tests/test_report_purchase.py`

**Interfaces:**
- Consumes: `ReportOrder`, report pricing, signed `EN_AT` session, and PortOne lookup service.
- Produces: `POST /esg/reports/{report_id}/orders` (server creates/reuses pending payment ID and amount); `POST /esg/orders/{payment_id}/complete` (server verifies PortOne payment); report detail returns the official URL only to a paid owner.

- [ ] **Step 1: Add failing endpoint tests**

Cover no session, ineligible report, missing PortOne configuration, server-calculated amount, PortOne `PAID` success, canceled/non-paid payment, amount/currency/payment-ID mismatch, unknown order, a different user completing the order, repeated completion, repeated order creation, and paid-only access URL.

- [ ] **Step 2: Run focused endpoint tests and verify failures**

Run: `..\..\.venv\Scripts\python.exe -m pytest tests/test_report_purchase.py -q --basetemp .pytest-tmp-esg-api`
Expected: FAIL until routes and authorization checks are implemented.

- [ ] **Step 3: Implement authenticated server-priced order creation**

Ignore all client price/report/user fields. Require the existing signed-in user, reject ineligible reports, and return a stable pending payment ID plus server amount and order name.

- [ ] **Step 4: Implement authoritative and idempotent completion**

Query PortOne using the stored payment ID; grant access only when payment ID, status `PAID`, total amount, and `KRW` currency match the stored order. Make a repeated successful completion return the already-confirmed result.

- [ ] **Step 5: Implement owner-only report URL release**

Return the official PDF URL (or official landing page if no direct PDF exists) only after purchase confirmation for that user. Preserve the public summary and source attribution without revealing the PDF address.

- [ ] **Step 6: Run focused endpoint tests**

Run: `..\..\.venv\Scripts\python.exe -m pytest tests/test_report_purchase.py -q --basetemp .pytest-tmp-esg-api`
Expected: PASS across authentication, payment verification, retry, and access-control cases.

### Task 5: Replace the PDF dialog with report detail navigation

**Files:**
- Create: `frontend/src/views/ReportDetailView.vue`
- Modify: `frontend/src/components/ReportCoverRail.vue`
- Modify: `frontend/src/views/EsgAtlasView.vue`
- Modify: `frontend/src/app-routing.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/api/esg.js`
- Modify: `frontend/src/style.css`
- Test: `frontend/src/report-purchase.test.js` (or existing frontend test module)

**Interfaces:**
- Consumes: `GET /esg/reports/{report_id}` safe detail response.
- Produces: stable detail route for each report; page shows company/title/year/summary/sources/page count/price and purchase state; successful confirmation displays a paid-only official source link.

- [ ] **Step 1: Add failing Jest tests for report detail behavior**

Cover summary and sources, formula display, unavailable state for null page count, no official URL before payment, and paid link only after backend detail refresh.

- [ ] **Step 2: Run the focused Jest test and verify failure**

Run: `npm test -- --runInBand src/report-purchase.test.js`
Workdir: `frontend`
Expected: FAIL because the detail page and route do not yet exist.

- [ ] **Step 3: Add detail-route navigation from report covers**

Replace the PDF dialog event with navigation using the stable report ID; ensure browser back returns to the atlas and direct detail URLs can load. Extend `app-routing.js` and `App.vue` so `/reports/{report_id}` loads the detail view directly and login can return to that URL.

- [ ] **Step 4: Implement the concise report detail page**

Fetch safe metadata from the backend and render source attribution, verified page count, server-calculated price, and purchase/paid/unavailable states. Do not render iframe PDF content.

- [ ] **Step 5: Run focused Jest tests**

Run: `npm test -- --runInBand src/report-purchase.test.js`
Workdir: `frontend`
Expected: PASS for route, page, metadata, and paid-only link behavior.

### Task 6: Connect PortOne V2 checkout and completion UX

**Files:**
- Create: `frontend/src/api/report-purchase.js`
- Create: `frontend/src/portone-payment.js`
- Modify: `frontend/src/views/ReportDetailView.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/.env.example`
- Test: `frontend/src/report-purchase.test.js`

**Interfaces:**
- Consumes: order and completion APIs; `VITE_PORTONE_STORE_ID`; `VITE_PORTONE_TOSSPAYMENTS_CHANNEL_KEY`; existing current-user session lookup.
- Produces: checkout through `@portone/browser-sdk/v2` and `PortOne.requestPayment` with server-created `paymentId`, amount, title, KRW, Toss channel key, and `CARD`; completion receives only the resulting payment ID.

- [ ] **Step 1: Add failing SDK/UX tests**

Assert request parameters come from server order response, no secret enters frontend, SDK cancel/error does not call successful completion, successful SDK response calls completion, and retry refreshes order status safely.

- [ ] **Step 2: Install the official browser SDK in the frontend package**

Run: `npm install @portone/browser-sdk`
Workdir: `frontend`
Expected: package and lock file include the official SDK; do not install or modify backend environment packages.

- [ ] **Step 3: Implement the V2 client and purchase interaction**

Use the V2 import path `@portone/browser-sdk/v2`; request only a one-time card payment through the environment-configured Toss V2 channel. Set `redirectUrl` to the current report detail URL and `forceRedirect: true` so mobile checkout is supported; on return, send only the returned `paymentId` to backend completion. A redirect containing a provider error must never call successful completion.

When the user is signed out, route to `/login` with the report detail destination preserved and return to that detail after login.

- [ ] **Step 4: Run focused Jest tests**

Run: `npm test -- --runInBand src/report-purchase.test.js`
Workdir: `frontend`
Expected: PASS for checkout arguments, cancel/failure behavior, and confirmation flow.

### Task 7: Verify the full feature and prepare integration

**Files:**
- Modify only files listed in Tasks 1 to 6.
- Preserve root-only uncommitted files outside the isolated worktree.

**Interfaces:**
- Consumes: completed feature branch and existing project test commands.
- Produces: reviewed, tested commit(s) on `work/esg-report-purchase`; no claim that real payment has passed without a configured Toss V2 test channel.

- [ ] **Step 1: Run full backend tests**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp-esg-full`
Expected: PASS for all backend tests.

- [ ] **Step 2: Run full frontend tests and production build**

Run: `npm test -- --runInBand`
Run: `npm run build`
Workdir: `frontend`
Expected: both commands exit 0.

- [ ] **Step 3: Review branch diff and commit feature work**

Run: `git diff --check` and inspect `git diff 39d52cb...HEAD`.
Expected: no secrets, no PortOne console changes, no unrelated root artifacts, all planned tests present; commit the completed feature.

- [ ] **Step 4: Report integration status accurately**

Confirm whether the feature branch can be merged into `main` without touching its existing uncommitted files. If a merge would overwrite/conflict with pre-existing local changes, leave those files intact and report the exact integration blocker. Do not push without validating branch state and remote authorization at that stage.

