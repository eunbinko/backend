# 공시 아틀라스 프론트엔드

Vue 3 + Vite로 만든 ESG 공시 지도와 보고서 구매 화면입니다.

## 실행

백엔드를 `http://127.0.0.1:8000`에서 실행한 뒤:

```powershell
cd frontend
npm install
npm run dev
```

Vue는 Axios와 Fetch를 통해 FastAPI에 직접 요청합니다. 개발 기본 API 주소는 `http://127.0.0.1:8000`이고, 배포 빌드는 `https://api.kkoi.kro.kr`을 사용합니다. 개발 환경에서는 `frontend/.env.local`의 `VITE_API_BASE`로 주소를 바꿀 수 있습니다. 백엔드는 브라우저 쿠키 요청을 허용하도록 프론트 출처를 CORS에 등록해야 합니다.

## 연결된 API

- `GET /board` — 최신 글 목록
- `GET /board/read/{idx}` — 글 상세
- `POST /board/register` — 글 등록
- `POST /user/signup` — 회원가입
- `POST /user/login` — 로그인 및 `EN_AT` HttpOnly 쿠키 발급

게시글 API는 현재 백엔드에서 로그인 없이도 사용할 수 있어, 계정 기능은 계정 메뉴에서 제공합니다.

## Kakao login configuration

Kakao login uses the JavaScript SDK in Vue and a FastAPI authorization-code callback. It requests only the `profile_nickname` consent item and identifies accounts by Kakao's service user ID. Kakao email is not requested or read, and Kakao identities are not automatically linked to local accounts.

Set local-only values in the repository root `.env` using `.env.example` as a guide:

- `KAKAO_REST_API_KEY`
- `KAKAO_CLIENT_SECRET` when the Kakao REST API key has client secret enabled
- `KAKAO_REDIRECT_URI=http://localhost:8000/user/kakao/callback`
- `FRONTEND_URL=http://localhost:5173`
- `FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

Set `VITE_API_BASE=http://127.0.0.1:8000` and `VITE_KAKAO_JAVASCRIPT_KEY` in `frontend/.env.local` using `frontend/.env.example`. Restart Vite after changing this file. Do not commit either local environment file.

The Kakao Developers app must have Kakao Login enabled, `http://localhost:5173` registered as a JavaScript SDK domain, and `http://localhost:8000/user/kakao/callback` registered as the redirect URI for the JavaScript and REST keys. Enable nickname consent; leave email without permission. The callback finishes at the Vue frontend using `FRONTEND_URL`.

## Nginx deployment

Vue API requests go directly to the backend origin. The deployment workflow builds with `VITE_API_BASE=https://api.kkoi.kro.kr`; local development uses `http://127.0.0.1:8000`. Since the origins differ, configure backend CORS to allow the frontend origin with credentials.

1. Build the frontend with `VITE_API_BASE=https://api.kkoi.kro.kr`:

   ```powershell
   cd frontend
   npm install
   npm run build
   ```

2. Copy the contents of `frontend/dist` to the Nginx document root, such as `/usr/share/nginx/html`.
3. Copy `nginx.conf.example` into the Nginx site configuration (or merge its `server` block into the existing site), then validate and reload Nginx with `nginx -t` and `nginx -s reload`.

The example listens on port 80 for `www.kkoi.kro.kr` and serves Vue routes through `index.html`. Configure HTTPS certificates for the frontend hostname in Nginx for production. The frontend and backend run independently; the frontend host does not proxy API requests.

Set backend `COOKIE_DOMAIN=kkoi.kro.kr` and `COOKIE_SECURE=true` in production. The backend must allow `https://www.kkoi.kro.kr` in `FRONTEND_ORIGINS` with credentials enabled. For local development, allow `http://127.0.0.1:5173` and `http://localhost:5173`. Set backend `FRONTEND_URL=https://www.kkoi.kro.kr` and `KAKAO_REDIRECT_URI=https://api.kkoi.kro.kr/user/kakao/callback`, then register that callback URL with Kakao. Both production sites must use HTTPS for secure cookies.
