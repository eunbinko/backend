# 모아 프론트엔드

Vue 3 + Vite로 만든 FastAPI 게시판 화면입니다.

## 실행

백엔드를 `http://127.0.0.1:8000`에서 실행한 뒤:

```powershell
cd frontend
npm install
npm run dev
```

Vue는 FastAPI에 직접 요청합니다. `frontend/.env.local`에 `VITE_API_BASE=http://localhost:8000`을 설정하고, 백엔드는 `FRONTEND_ORIGINS=http://localhost:5173`에 지정된 프론트 출처의 쿠키 요청을 허용해야 합니다. API 주소나 개발 출처를 바꾸면 두 설정을 함께 수정하세요. 직접 브라우저 요청에는 자격 증명을 포함하며, 배포에서는 HTTPS와 허용 출처를 배포 주소로 설정하세요.

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

Set `VITE_API_BASE=http://localhost:8000` and `VITE_KAKAO_JAVASCRIPT_KEY` in `frontend/.env.local` using `frontend/.env.example`. Restart Vite after changing this file. Do not commit either local environment file.

The Kakao Developers app must have Kakao Login enabled, `http://localhost:5173` registered as a JavaScript SDK domain, and `http://localhost:8000/user/kakao/callback` registered as the redirect URI for the JavaScript and REST keys. Enable nickname consent; leave email without permission. The callback finishes at the Vue frontend using `FRONTEND_URL`.
