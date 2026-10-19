# 모아 프론트엔드

Vue 3 + Vite로 만든 FastAPI 게시판 화면입니다.

## 실행

백엔드를 `http://127.0.0.1:8000`에서 실행한 뒤:

```powershell
cd frontend
npm install
npm run dev
```

Vite 개발 서버는 `/api` 요청을 FastAPI에 전달하고 `/api` 접두사를 제거합니다. 배포 환경에서는 같은 출처에서 `/api`를 백엔드로 프록시하도록 설정하거나 `VITE_API_BASE`를 백엔드 API 주소로 지정하세요. 쿠키 인증을 위해 프론트와 API의 출처/CORS 및 HTTPS 설정을 함께 맞춰야 합니다.

## 연결된 API

- `GET /board` — 최신 글 목록
- `GET /board/read/{idx}` — 글 상세
- `POST /board/register` — 글 등록
- `POST /user/signup` — 회원가입
- `POST /user/login` — 로그인 및 `EN_AT` HttpOnly 쿠키 발급

게시글 API는 현재 백엔드에서 로그인 없이도 사용할 수 있어, 계정 기능은 계정 메뉴에서 제공합니다.
