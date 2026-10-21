# Disclosure Atlas Frontend

Vue 3 and Vite frontend for the ESG disclosure atlas and report purchase flow.

## Local development

Start FastAPI on `http://127.0.0.1:8000`, then run:

```powershell
cd frontend
npm install
npm run dev
```

For local development, set `VITE_API_BASE=http://127.0.0.1:8000` in `frontend/.env.local`. The frontend sends requests directly to that FastAPI address. Production builds use `https://api.kkoi.kro.kr` through the deployment workflow's `VITE_API_BASE` setting.

## Authentication and Kakao

Local-only values belong in ignored `.env` files:

- Root `.env`: `KAKAO_REST_API_KEY`, and `KAKAO_CLIENT_SECRET` when enabled in Kakao Developers.
- `frontend/.env.local`: `VITE_KAKAO_JAVASCRIPT_KEY`.

Register `http://localhost:8000/user/kakao/callback` and `https://api.kkoi.kro.kr/user/kakao/callback` as Kakao redirect URIs. Register `http://localhost:5173` and `https://www.kkoi.kro.kr` as JavaScript SDK domains. Enable the `profile_nickname` consent item. Kakao email is not requested.

The browser sends credentialed requests directly to the API. Configure FastAPI `FRONTEND_ORIGINS` with the frontend origins and `FRONTEND_URL` with the public frontend address. For production, set `COOKIE_SECURE=true`, and set `COOKIE_DOMAIN=kkoi.kro.kr` when the frontend and API use the `www` and `api` subdomains. Cookies use `HttpOnly` and `SameSite=Lax`.

Set the production backend values in its `.env`: `FRONTEND_URL=https://www.kkoi.kro.kr`, `FRONTEND_ORIGINS=https://www.kkoi.kro.kr`, `KAKAO_REDIRECT_URI=https://api.kkoi.kro.kr/user/kakao/callback`, `COOKIE_SECURE=true`, and `COOKIE_DOMAIN=kkoi.kro.kr`.

## Production API connection

The frontend is served as a static site. Axios uses `VITE_API_BASE=https://api.kkoi.kro.kr` and calls FastAPI routes such as `/user/me` and `/esg/companies` directly. The deployment workflow embeds this address in the frontend build; no `/api` reverse-proxy rule or proxy snippet is published by the frontend deployment.

The API server must present a trusted TLS certificate for `api.kkoi.kro.kr` and allow the frontend origin through credentialed CORS. Configure Kakao's REST redirect URI as `https://api.kkoi.kro.kr/user/kakao/callback`.

## Tests and build

```powershell
npm test -- --runInBand
npm run build
```
