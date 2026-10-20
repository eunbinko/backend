# ESG Report Purchase Design

## Goal

Replace the ESG report PDF popup with a concise report detail page and let signed-in users purchase app access to a report through PortOne V2 and Toss Payments' new module.

## Agreed Constraints

- Use the existing ESG report source records and official report URLs; do not copy PDFs to this server in this phase.
- Do not change any existing PortOne console settings. Configure the application to use environment-provided PortOne V2 Store ID, Toss Payments new-module channel key, and V2 API secret.
- The PortOne console currently has no registered channel in either live or test mode. The application can be implemented, but an actual payment flow cannot be verified until a Toss Payments V2 test channel is provisioned.
- Do not expose or inspect PortOne API secrets in the console.
- Work in the main agent only; do not delegate to subagents.
- Preserve the pre-existing uncommitted Kakao authentication work in the main worktree and exclude it from feature commits.

## User Experience

- Clicking a report cover opens a report detail page in the application instead of the current PDF viewer popup.
- The page shows the company name, report title and year, a short ESG summary, verified report source, verified page count, calculated price, and purchase state.
- Use the company's existing ESG highlights as the concise summary; keep attribution links visible.
- A signed-in user can purchase an eligible report. An unsigned user is directed to login and returned to the report detail page afterward.
- After the server confirms payment, show an in-app link to the official report PDF when a direct PDF URL exists. For a report that only has an official landing page, link to that official page after purchase.
- Show clear pending, canceled, failed, already-purchased, and verification-error states. Repeated clicks must not create duplicate paid entitlements.

## Pricing and Eligibility

- Price is `ceil(page_count / 100) * 1000` KRW. Thus, any report of 1 to 100 pages costs 1,000 KRW, 101 to 200 pages costs 2,000 KRW, and so forth.
- Page count is report metadata sourced from the official PDF and must be verified before the report is purchasable.
- If there is no direct PDF or the page count cannot be verified, do not guess the price; disable purchase and show that online purchase is unavailable for that report.
- Existing records with no direct PDF remain viewable as summary/source pages, but are not purchasable until a verifiable PDF and page count are available.

## Architecture and Data Flow

### Frontend

- Replace `ReportPdfDialog` with a report detail view, reachable from cover cards and addressable by a stable report route.
- Add a small PortOne V2 client module that imports `@portone/browser-sdk/v2` and supplies the configured Store ID and Toss Payments V2 channel key. Do not put the API secret in frontend configuration.
- Ask the backend to create or reuse a pending order before invoking `PortOne.requestPayment`. Use the server-returned `paymentId`, amount, currency, and report title. Request a supported one-time payment method.
- Send only the resulting `paymentId` to the backend completion endpoint. Do not trust amount, report, user, or success state sent from the browser.
- On browser cancellation or SDK error, keep the user on the detail page and show a retryable status.

### Backend

- Add a report detail API that returns safe report metadata, short summary, sources, page count, calculated amount, and current user's purchase state. Never return API credentials.
- Add a persistent order model linked to user and report, with a unique PortOne `payment_id`, immutable KRW amount, creation time, and status (`PENDING`, `PAID`, or `FAILED`). Enforce one paid entitlement per user/report.
- Require authenticated users to create an order. Calculate amount from verified server-side report metadata; ignore any client-supplied price.
- Complete an order by querying PortOne V2 `GET /payments/{paymentId}` with the server-only API secret. Mark an order paid only when PortOne reports `PAID`, the payment ID matches, total amount equals the stored order amount, and currency is KRW. Reject unknown orders, mismatched user ownership, non-paid results, and mismatched amounts. Make completion idempotent.
- A pending order can be retried with the same payment ID; do not create a second paid entitlement for an already-purchased report.
- Add environment settings for Store ID, Toss Payments V2 channel key, and V2 API secret. Missing settings must produce a clear configuration error on order creation/completion, not a fake success.
- Use the existing cookie-based authentication and SQLite SQLAlchemy conventions.

## Access and Content Protection

- Only the purchased user sees the in-app link to the official PDF or official report landing page.
- Since the current data uses public third-party URLs and PDFs remain hosted by report issuers, the app cannot enforce secrecy or prevent copying/sharing those source URLs. This phase does not proxy, download, or store PDF content. Server-hosted protected PDF delivery is explicitly deferred.

## Failure Handling and Security

- PortOne SDK errors and cancellation are user-visible but do not mark an order paid.
- PortOne API network errors leave the order pending and can be retried safely.
- PortOne status/amount/currency mismatches never grant access and are recorded as failed or left pending according to the actual authoritative status.
- Keep the PortOne V2 API secret server-side in an environment variable; do not log secrets or expose them in API responses.
- Do not configure or modify PortOne webhooks in this phase because no channel is currently registered and the user asked to preserve console settings. Payment completion verification uses a server-side PortOne API lookup.

## Testing and Acceptance

- Backend pytest coverage: report eligibility and page-count pricing; unauthenticated order rejection; server-derived order amount; PortOne API success, cancellation, failure, network error, amount/currency mismatch, unknown payment ID, user mismatch, duplicate completion, and already-purchased report.
- Frontend Jest coverage: detail view summary and price; unavailable purchase when page count is absent; redirect behavior for signed-out users; PortOne SDK request parameters; cancel/error/retry behavior; paid link visibility only after backend confirmation.
- Existing backend pytest and frontend Jest suites must pass.
- Build the Vue frontend and run the full pytest suite using the project's intended Python environment.
- Verify the implementation does not modify the existing PortOne console configuration. Actual PG checkout acceptance remains blocked until a Toss Payments V2 test channel and valid server API secret are made available.

## Out of Scope

- Downloading/copying PDFs to the server, proxying PDF bytes, or preventing direct access through issuer URLs.
- Refund processing, subscriptions, recurring charges, receipts, tax invoices, and webhook configuration.
- Creating or changing a PortOne PG channel or merchant credentials in the PortOne console.
