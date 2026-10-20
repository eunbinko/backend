# Kakao JavaScript Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add Kakao login to the Vue application using Kakao's JavaScript SDK, storing only the Kakao service user ID and nickname.

**Architecture:** Vue calls `Kakao.Auth.authorize()` with only `profile_nickname` consent and redirects to a FastAPI callback. FastAPI validates a browser-bound one-time state, exchanges the authorization code, verifies the Kakao profile server-side, creates or finds an `OAuthAccount`, and issues the existing HttpOnly `EN_AT` cookie. SQLite migration makes local user email nullable while preserving existing local accounts.

**Tech Stack:** FastAPI, SQLAlchemy 2, SQLite, PyJWT, Vue 3, Vite, Kakao JavaScript SDK, pytest, Jest.

**Spec:** `docs/superpowers/specs/2026-10-20-kakao-javascript-login-design.md`

## Global Constraints

- Request only Kakao's `profile_nickname` consent scope; do not request, store, or compare email.
- Identify Kakao accounts by the unique pair `(provider, provider_user_id)`.
- Keep the Kakao REST API key on the backend; the JavaScript key is public frontend configuration.
- Do not persist Kakao authorization codes or access tokens in browser storage or logs.
- Preserve local email/password signup and login behavior and existing `EN_AT` cookie attributes.
- Verify callback state before exchanging the code or changing the database.
- Backend pytest and frontend Jest suites must both pass before completion.

## Review Focus

- Kakao cancellation or provider error: return to `/login` with a safe message and create no user or cookie (Task 3 callback rejection tests).
- Profile without a numeric/string Kakao ID or non-empty nickname: reject without persisting an account (Task 3 provider-profile tests).
- Two first-login callbacks for the same Kakao ID: keep one user and one OAuth identity, then issue a valid session for the winner (Task 3 concurrency test).
- Existing SQLite user table: migration preserves IDs, emails, password hashes, and the unique email index (Task 1 migration test).
- Missing frontend JavaScript key or blocked SDK script: keep email/password controls usable and show an accessible Kakao-specific error (Task 4 frontend tests).

---

### Task 1: Support Kakao identities in SQLite without breaking local accounts

**Files:**
- Modify: `app/models/user.py`
- Create: `app/models/oauth_account.py`
- Modify: `app/models/__init__.py`
- Create: `app/db/migrations.py`
- Modify: `app/main.py`
- Test: `tests/test_auth_migration.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Produces `OAuthAccount(user_id: int, provider: str, provider_user_id: str)` with a unique constraint on `(provider, provider_user_id)`.
- Produces `migrate_sqlite_user_email_nullable(engine) -> None`, called before `Base.metadata.create_all`.
- `User.email` becomes nullable but remains unique for non-null local addresses.

- [x] **Step 1: Write the migration test against the current schema**

Create a temporary SQLite database using the current `user(idx, email NOT NULL, password, name)` schema and `ix_user_email` unique index. Insert a local user, run app startup/migration, then assert the same `idx`, email, name, password hash, and unique index remain; assert a second row with `email=None` can be inserted.

- [x] **Step 2: Run the focused migration test and confirm it fails**

Run: `pytest tests/test_auth_migration.py -q`
Expected: FAIL because the migration function and OAuth model do not exist.

- [x] **Step 3: Implement nullable email, OAuthAccount, and idempotent SQLite migration**

Use a SQLite table rebuild in a transaction only when `PRAGMA table_info(user)` reports email as NOT NULL. Preserve `idx`, `email`, `password`, and `name`; recreate the existing unique `ix_user_email` index. Import `OAuthAccount` before metadata creation. Leave non-SQLite engines unchanged and raise a clear error if the migration cannot preserve the existing schema.

- [x] **Step 4: Run migration and local-auth tests**

Run: `pytest tests/test_auth_migration.py tests/test_auth.py -q`
Expected: PASS, including existing local signup/login and duplicate-email behavior.

### Task 2: Add Kakao configuration, SDK callback security, and token identity support

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/core/security.py`
- Create: `app/services/kakao.py`
- Modify: `app/api/routers/user.py`
- Modify: `app/main.py`
- Test: `tests/test_kakao_auth.py`
- Modify: `requirements.txt`

**Interfaces:**
- Settings: `KAKAO_REST_API_KEY`, `KAKAO_REDIRECT_URI`, `KAKAO_STATE_TTL_SECONDS` (default 300).
- `POST /user/kakao/state` creates a cryptographically random state, sets a short-lived HttpOnly/SameSite=Lax cookie, and returns the same state for the SDK authorize call.
- `GET /user/kakao/callback?code=...&state=...` validates and consumes the matching state, exchanges the code, authenticates the profile, sets `EN_AT`, and redirects to `/`.
- `KakaoOAuthClient.exchange_code(code: str) -> str` and `KakaoOAuthClient.get_profile(access_token: str) -> KakaoProfile` isolate provider HTTP requests for deterministic tests.
- `KakaoProfile(provider_user_id: str, nickname: str)` contains only Kakao ID and nickname.
- `createToken(user_id: str)` remains the JWT signing function; local login now passes `str(user.idx)` so all cookie subjects identify internal users.

- [x] **Step 1: Write failing tests for state and token identity**

Assert state endpoint returns a state and a secure-by-settings HttpOnly, SameSite=Lax, five-minute state cookie; callback rejects missing/mismatched/replayed state without calling Kakao; local login JWT `sub` equals the internal user ID.

- [x] **Step 2: Run focused tests and confirm they fail**

Run: `pytest tests/test_kakao_auth.py -q`
Expected: FAIL because endpoints/state handling are not implemented.

- [x] **Step 3: Implement signed session cookie issuance for the internal user ID**

Update local login token subject to `str(user.idx)` and retain the current 30-minute expiration and `EN_AT` cookie flags. Add a helper to issue that same cookie after Kakao login.

- [x] **Step 4: Implement Kakao configuration, one-time state, and provider client**

Use a short-lived signed state cookie with a random state and `max_age=KAKAO_STATE_TTL_SECONDS`; compare in constant time, clear it on every callback attempt, and reject missing/expired/mismatched state before provider calls. Use `httpx` with explicit timeouts, URL-encoded token exchange at `https://kauth.kakao.com/oauth/token`, and bearer-authenticated profile lookup at `https://kapi.kakao.com/v2/user/me`. Parse only `id` and `kakao_account.profile.nickname` (with the documented profile fallback if present); never read email fields.

- [x] **Step 5: Run focused state and callback tests**

Run: `pytest tests/test_kakao_auth.py -q`
Expected: PASS for valid state and rejection of invalid/replayed state. Provider exchange tests are completed in Task 3.

### Task 3: Create or retrieve Kakao accounts and finish the callback

**Files:**
- Modify: `app/api/routers/user.py`
- Modify: `app/services/kakao.py`
- Modify: `app/schemas/user.py`
- Test: `tests/test_kakao_auth.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- `get_or_create_kakao_user(db: Session, profile: KakaoProfile) -> User` queries by `provider="kakao"` and Kakao ID, creates `User(email=None, password=hash_password(secrets.token_urlsafe(48)), name=nickname)` plus `OAuthAccount` transactionally when absent, and safely resolves a uniqueness race by reloading the winner.
- Kakao callback redirects to `/` on success and `/login?social_error=kakao` on failure. Error URLs contain no provider code, token, or exception text.
- Local `UserResult.email` is nullable in response schema only where a user response can represent a Kakao account; local signup validation remains required and unchanged.

- [x] **Step 1: Write mocked provider/profile and account lifecycle tests**

Cover new Kakao user creation with null email, nickname storage, unique provider identity, repeat login resolving to the same user, rejecting malformed profiles, and ensuring email fields in mocked provider responses are ignored. Assert no `EN_AT` cookie and no database row on provider failure.

- [x] **Step 2: Run the focused lifecycle tests and confirm they fail**

Run: `pytest tests/test_kakao_auth.py -q`
Expected: FAIL because account creation and callback processing are not implemented.

- [x] **Step 3: Implement atomic account creation and race recovery**

Commit the user and OAuth identity in one transaction. On unique-identity `IntegrityError`, roll back and reload the identity; do not create a second user. Reject absent ID or blank/oversized nickname with no writes.

- [x] **Step 4: Connect callback, cookie, redirects, and nullable response schema**

After state validation, exchange the code, fetch the profile, call `get_or_create_kakao_user`, set `EN_AT` with the existing 1800-second HttpOnly/SameSite/Secure settings, then redirect. On Kakao cancellation, state failure, or provider exception, redirect safely to the login error marker without setting a cookie.

- [x] **Step 5: Run all backend tests**

Run: `pytest -q`
Expected: PASS, including the full existing local-auth and board tests plus mocked Kakao tests.

### Task 4: Add Kakao SDK login flow and Jest coverage to Vue

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/vite.config.js`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/jest.config.js`
- Create: `frontend/src/__tests__/kakao-login.test.js`
- Modify: `frontend/README.md`

**Interfaces:**
- Vite public setting: `VITE_KAKAO_JAVASCRIPT_KEY`.
- Local public redirect URI: `http://localhost:5173/api/user/kakao/callback`; Vite proxies this path to FastAPI and removes `/api` so the callback response sets the cookie for the frontend's `localhost` origin.
- Login click flow: POST `/user/kakao/state`, then call `Kakao.Auth.authorize({ redirectUri, scope: 'profile_nickname', state })`.
- Kakao callback error marker is read on `/login`; display a generic accessible error and remove the marker from browser history.
- SDK loads asynchronously; if the key is missing or the SDK fails to load, the Kakao button is disabled and an accessible configuration error is shown while password login remains available.

- [x] **Step 1: Add Jest and Vue test setup with a passing smoke test**

Add a `test` script using Jest, Vue SFC transform, and jsdom. Point the Vite `/api` proxy at `http://127.0.0.1:8000`, matching the existing frontend run instructions. Add a test that mounts the login page and confirms the local login fields remain present.

- [x] **Step 2: Run the frontend test and confirm configuration is incomplete**

Run: `npm test -- --runInBand`
Workdir: `frontend`
Expected: FAIL until Jest and Vue transforms are configured.

- [x] **Step 3: Implement Kakao SDK initialization and login button**

Load the Kakao JavaScript SDK once, initialize with `VITE_KAKAO_JAVASCRIPT_KEY`, obtain backend state before redirecting, request only `profile_nickname`, guard double clicks, and surface API/SDK errors via `role="alert"`. Do not store access tokens or authorization codes in local/session storage.

- [x] **Step 4: Implement callback error display and document configuration**

Show the Kakao error marker accessibly, remove it using `history.replaceState`, and document `VITE_KAKAO_JAVASCRIPT_KEY`, backend environment variables, the registered local domain/callback URI, and console settings.

- [x] **Step 5: Add and run frontend Jest behavior tests**

Test state request and `authorize` arguments (scope exactly `profile_nickname`), provider callback error display, missing key/SDK failure, and that local login remains available.

Run: `npm test -- --runInBand`
Workdir: `frontend`
Expected: PASS.

### Task 5: Configure Kakao Developers app and verify the browser flow

**Files:**
- Modify Kakao Developers app `mlops` (ID `1614696`) through Chrome DevTools.
- No repository files; record resulting non-secret configuration in `frontend/README.md`.

**Interfaces:**
- Enable Kakao Login.
- Add JavaScript SDK allowed domain `http://localhost:5173` for local Vite development.
- Register exact callback `http://localhost:5173/api/user/kakao/callback`; Vite proxies it to FastAPI's `/user/kakao/callback` so the browser stores `EN_AT` for `localhost`.
- Enable nickname consent only; leave email unrequested.
- Configure Vite JavaScript key as a local `VITE_KAKAO_JAVASCRIPT_KEY`; configure backend REST API key and the same exact `KAKAO_REDIRECT_URI` in local environment without committing secrets.

- [x] **Step 1: Verify app keys without copying secrets into logs or source control**

Read JavaScript and REST API keys from app `mlops` only to place them in the appropriate local environment settings; never print them in command output or commit them.

- [x] **Step 2: Apply and verify app settings in Chrome DevTools**

Enable Kakao Login, add the JavaScript SDK domain, register the callback URI, and set nickname as the only requested scope. Confirm dashboard settings show Login enabled and nickname consent configured; do not enable email consent.

- [x] **Step 3: Run a live browser login smoke check**

With backend and Vite running, use Chrome DevTools to verify the consent screen asks only for nickname, callback creates a nullable-email user, repeat login resolves to the same Kakao identity, and `EN_AT` is set. Do not capture or report authorization codes or Kakao tokens.

- [x] **Step 4: Run final regression suites**

Run: `pytest -q`
Run: `npm test -- --runInBand`
Run: `npm run build`
Expected: all pass.
