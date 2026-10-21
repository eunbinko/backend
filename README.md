# ESG 공시 지도

국내 주요 기업의 ESG 공시와 기업 정보를 지도에서 살펴보고, 보고서 상세 정보와 구매 기능을 이용할 수 있는 웹 애플리케이션입니다. Vue 3 프론트엔드와 FastAPI 백엔드로 구성되어 있으며 SQLite에 계정, 기업, 보고서, 주문 데이터를 저장합니다.

## 주요 기능

- 2025 회계연도 매출 기준 기업 목록과 본사 위치를 지도에서 확인
- 기업별 ESG 핵심 정보와 공시 출처 및 검증일 확인
- ESG 보고서 상세 정보와 페이지 수 기반 가격 확인
- 회원 가입, 이메일 로그인, 로그아웃 및 카카오 로그인
- PortOne 결제를 통한 보고서 주문 및 구매 후 접근
- 기존 게시판 글 목록, 상세 조회, 등록

## 기술 스택

- 프론트엔드: Vue 3, Vite, Leaflet
- 백엔드: Python, FastAPI, SQLAlchemy
- 데이터베이스: SQLite (기본 파일 `db.sqlite`)
- 인증: HttpOnly 쿠키, JWT, 카카오 OAuth
- 결제: PortOne Browser SDK

## 로컬 실행

Python 의존성을 설치하고 저장소 루트에서 백엔드를 실행합니다.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

별도 터미널에서 프론트엔드를 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

프론트엔드는 `http://localhost:5173`, 백엔드는 `http://127.0.0.1:8000`에서 실행됩니다. FastAPI 문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다. 백엔드 시작 시 테이블을 준비하고 ESG 기업 데이터를 데이터베이스에 반영합니다.

## 환경 변수

저장소 루트의 `.env.example`을 참고해 `.env`를 만들고, `frontend/.env.example`을 참고해 `frontend/.env.local`을 만듭니다.

루트 `.env`에서 사용하는 값:

| 변수 | 설명 |
| --- | --- |
| `SECRET_KEY` | JWT 서명 키. 운영 환경에서는 충분히 긴 무작위 값을 지정합니다. |
| `DATABASE_URL` | SQLite 연결 문자열. 기본값은 `sqlite:///db.sqlite`입니다. |
| `COOKIE_SECURE` | HTTPS 운영 환경에서 `true`로 설정합니다. |
| `FRONTEND_URL` | 카카오 로그인 완료 후 이동할 프론트엔드 주소 |
| `FRONTEND_ORIGINS` | 쿠키 요청을 허용할 프론트엔드 출처 목록(쉼표 구분) |
| `KAKAO_REST_API_KEY` | 카카오 앱의 REST API 키 |
| `KAKAO_CLIENT_SECRET` | 카카오 앱에서 Client Secret을 활성화한 경우 사용 |
| `KAKAO_REDIRECT_URI` | 카카오 로그인 콜백 주소 |
| `PORTONE_STORE_ID` | PortOne 상점 식별자 |
| `PORTONE_TOSSPAYMENTS_CHANNEL_KEY` | PortOne 토스페이먼츠 채널 키 |
| `PORTONE_API_SECRET` | 결제 검증용 PortOne API Secret |

`frontend/.env.local`에서는 개발 백엔드 주소를 `VITE_API_BASE=https://api.kkoi.kro.kr`으로 설정하고, `VITE_KAKAO_JAVASCRIPT_KEY`에 카카오 JavaScript 키를 입력합니다. 배포 워크플로는 `https://api.kkoi.kro.kr`을 API 주소로 사용합니다. 결제 설정에는 `VITE_PORTONE_STORE_ID`, `VITE_PORTONE_TOSSPAYMENTS_CHANNEL_KEY`도 필요합니다. 환경 변수를 변경한 뒤에는 해당 개발 서버를 재시작하세요.

카카오 개발자 콘솔에서 카카오 로그인을 활성화하고 JavaScript SDK 도메인과 위 콜백 URI를 등록해야 합니다. 로그인은 닉네임 정보만 사용하며 카카오 이메일을 요청하지 않습니다. 프론트엔드와 백엔드 주소가 달라지면 CORS 허용 출처와 리다이렉트 설정도 함께 변경하세요.

## 주요 API

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/esg/companies?fiscal_year=2025` | ESG 기업 및 보고서 목록 |
| `GET` | `/esg/reports/{report_id}` | 보고서 상세 정보와 구매 여부 |
| `POST` | `/esg/reports/{report_id}/orders` | 로그인 사용자의 보고서 주문 생성 |
| `POST` | `/esg/orders/{payment_id}/complete` | 결제 결과 검증 및 주문 완료 |
| `POST` | `/user/signup` | 이메일 회원 가입 |
| `POST` | `/user/login` | 이메일 로그인 및 `EN_AT` 쿠키 발급 |
| `GET` | `/user/me` | 현재 로그인 사용자 조회 |
| `POST` | `/user/logout` | 로그아웃 및 쿠키 삭제 |
| `POST` | `/user/kakao/state` | 카카오 로그인 CSRF 상태값 생성 |
| `GET` | `/user/kakao/callback` | 카카오 로그인 콜백 |
| `GET` | `/board` | 게시글 목록 |
| `GET` | `/board/read/{idx}` | 게시글 상세 |
| `POST` | `/board/register` | 게시글 등록 |

## 검증

백엔드 테스트:

```powershell
python -m pytest -q
```

프론트엔드 테스트:

```powershell
cd frontend
npm test
```

프론트엔드 프로덕션 빌드:

```powershell
cd frontend
npm run build
```

## GitHub Actions 배포

`app/**` 또는 `requirements.txt`가 `main`에 반영되면 백엔드 워크플로가 실행되고, `frontend/**`가 반영되면 프론트엔드 워크플로가 실행됩니다. 두 워크플로는 `.github/workflows`에 있으며 `workflow_dispatch`로 수동 실행할 수도 있습니다.

저장소의 **Settings → Secrets and variables → Actions → New repository secret**에서 다음 값을 등록하세요.

| Secret | 값 |
| --- | --- |
| `SSH_HOST` | 서버 주소 (예: `222.112.208.68`) |
| `SSH_USERNAME` | SSH 계정 |
| `SSH_PASSWORD` | SSH 비밀번호 |
| `BACKEND_DEPLOY_PATH` | 서버의 백엔드 배포 디렉터리 (예: `/opt/disclosure-atlas/backend`) |
| `FRONTEND_DEPLOY_PATH` | 서버의 프론트엔드 배포 디렉터리 (예: `/opt/disclosure-atlas/frontend`) |
| `BACKEND_SSH_PORT` | 백엔드 SSH 접속 포트. 생략 시 `9105` |
| `FRONTEND_SSH_PORT` | 프론트엔드 SSH 접속 포트. 생략 시 `9005` |

두 SSH 포트 Secret은 별도로 둘 수 있으며, 같은 SSH 포트를 사용한다면 두 Secret에 같은 값을 입력하세요. 서버에는 Python 3, Node.js/npm, SSH 접속 권한이 필요합니다. SSH 계정은 배포 디렉터리를 생성하고 쓸 수 있어야 하며, 서버 방화벽은 SSH 포트와 서비스 포트 `9105`(백엔드), `9005`(프론트엔드)의 접근을 허용해야 합니다. 각 워크플로는 해당 디렉터리의 `.venv`/`node_modules`를 사용하고 프로세스 PID 파일과 로그 파일을 유지하며 서비스를 재시작합니다. 서버의 `.env`와 SQLite DB는 배포 경로에 별도로 준비하세요.
