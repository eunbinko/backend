# Kakao JavaScript Login Design

## Goal

Add Kakao login to the Vue application using the Kakao JavaScript SDK. Kakao users are identified only by Kakao's stable service user ID; the application requests and stores the nickname but does not request or store email.

## Context

The application has a FastAPI backend, Vue 3 frontend, and SQLite database. Local accounts use a unique email and password hash. Successful local login issues a signed `EN_AT` HttpOnly cookie. The current user model requires an email, so it cannot represent a Kakao-only account without a schema change.

## Decisions

1. The login page initializes Kakao JavaScript SDK with a public JavaScript key supplied through `VITE_KAKAO_JAVASCRIPT_KEY`.
2. The Kakao button calls `Kakao.Auth.authorize()` and requests only the `profile_nickname` consent scope. The registered redirect URI points to a FastAPI callback.
3. The callback exchanges the authorization code using the backend-only Kakao REST API key, retrieves Kakao user information, and uses only Kakao service user ID and nickname. Email is neither requested nor consumed.
4. There is no email collision check or automatic linking. A local user and a Kakao user remain distinct identities because Kakao email is not collected.
5. Add an `OAuthAccount` table with a unique `(provider, provider_user_id)` identity and a foreign key to `User`. New Kakao users have a nullable `User.email`, a generated unusable password hash, and the Kakao nickname as their name. Existing local account emails remain unique.
6. Issue the existing `EN_AT` HttpOnly cookie on successful Kakao login. Tokens identify application users by the stable internal user ID so users without an email can be represented. Local login continues to find accounts by email.
7. OAuth state must be unpredictable, bound to the browser, short-lived, and checked once in the callback. Provider errors, invalid state, failed token exchange, failed profile lookup, missing ID, and missing nickname must not create an account or issue a cookie.
8. The Vue login page displays Kakao login success/failure through the existing user-facing status/error patterns. The SDK access token and authorization code are not persisted in browser storage.

## API and Flow

1. Vue loads the Kakao JavaScript SDK, initialized with the JavaScript key from Vite configuration.
2. User activates Kakao login. The SDK requests `profile_nickname` and redirects to the configured backend callback with an authorization code and state.
3. FastAPI validates and consumes the state, exchanges the code at Kakao's token endpoint using the REST API key and exact redirect URI, then calls Kakao's user information endpoint with the access token.
4. FastAPI looks up `(provider="kakao", provider_user_id=<Kakao user ID>)`. If found, it logs in the linked user. Otherwise, it creates a user with no email and creates the OAuth identity in one transaction.
5. FastAPI sets the normal `EN_AT` cookie and redirects to the Vue home page. Any error redirects to the login page with a safe, non-sensitive failure marker.

## Data and Migration

- Change `User.email` to nullable while keeping it unique. SQLite permits multiple NULL values under a unique constraint.
- Add `OAuthAccount` with primary key, `user_id` foreign key, provider, provider user ID, and a unique constraint on `(provider, provider_user_id)`.
- Application startup currently uses `Base.metadata.create_all`, which does not alter existing columns. Add a safe SQLite migration/startup migration that rebuilds the existing `user` table while preserving all local rows and indexes, or use an established migration tool if one is added. The chosen approach must be covered by a test that starts from the current schema and preserves existing user credentials.

## Security and Failure Behavior

- Never trust a user ID or nickname supplied by Vue. Use only the profile returned by Kakao after backend token exchange.
- Keep the REST API key server-side; expose only the JavaScript key in the frontend build.
- Do not log authorization codes, Kakao tokens, or secrets.
- Reject state mismatches, expired/replayed states, provider cancellation, provider API errors, malformed profiles, and missing required nickname or ID without issuing `EN_AT`.
- Handle concurrent first logins for the same Kakao identity without duplicate users or unhandled integrity errors.
- Preserve the current local email/password signup and login behavior.

## Configuration and Operations

- Backend: `KAKAO_REST_API_KEY`, `KAKAO_REDIRECT_URI`.
- Frontend: `VITE_KAKAO_JAVASCRIPT_KEY`.
- Kakao Developers app: enable Kakao Login, allow the JavaScript SDK domain, register the exact redirect URI, and enable the nickname consent item. Do not enable or request Kakao email for this feature.
- Keep secrets out of source control and document local environment setup.

## Testing

- Backend pytest coverage: state lifecycle and callback rejection, mocked token/profile exchange, existing/new Kakao identity, duplicate/concurrent first login, missing nickname/ID, cookie claims, local-auth regression, and migration preservation from the current SQLite schema.
- Frontend Jest coverage: SDK setup and Kakao button initiation, callback success/failure behavior, and error/status display. Test without calling Kakao's live service.
- The full backend pytest suite and frontend Jest suite must pass.

## Out of Scope

- Kakao email consent, email-based account collision checks, and linking Kakao identities to local accounts.
- Kakao logout/unlink and account deletion workflows.
- Google or other social providers.
- Changing board ownership or requiring login for board operations.
