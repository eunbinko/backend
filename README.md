# 회원가입·로그인 애플리케이션

FastAPI와 SQLite를 사용하는 백엔드와 Vue 기반 프론트엔드 프로젝트입니다.

## 실행

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

기본 DB는 실행 디렉터리의 `db.sqlite`이며 앱 시작 시 테이블과 이메일 고유 인덱스를 생성합니다.
API 문서는 `/docs`에서 확인할 수 있습니다.

`.env`에서 `DATABASE_URL`, `SECRET_KEY`, `COOKIE_SECURE`를 설정할 수 있습니다.
지속적인 토큰 검증과 여러 프로세스 사용 시 동일한 32바이트 이상의 무작위 `SECRET_KEY`를 설정하세요.
미설정 시 프로세스마다 임시 키를 생성합니다. HTTPS 환경에서는 `COOKIE_SECURE=true`를 사용하세요.

## API

- `POST /user/signup`: `email`, `password`, `name`을 받아 201 반환
- `POST /user/login`: `email`, `password`를 받아 200 반환, 30분 유효한 JWT를 `EN_AT` HttpOnly 쿠키로 발급
- 성공 응답: `{"code": 201, "result": {"email": "member@example.com", "name": "회원"}}`
- 오류 응답: `{"code": 409, "result": "이미 가입한 이메일입니다."}`
- 이메일 중복은 409, 로그인 정보 불일치는 401, 잘못된 입력은 422

명세의 `passord`는 `password`로 해석했습니다. 이메일은 앞뒤 공백 제거 및 소문자 변환,
이름은 앞뒤 공백 제거를 적용합니다. 비밀번호는 1~128자이며 입력 그대로 해시합니다.
비밀번호는 PBKDF2-SHA256(600,000회, 사용자별 무작위 salt)으로 저장하며 응답에 포함하지 않습니다.

기존 평문 비밀번호 계정은 보안상 로그인되지 않습니다. 기존 데이터의 자동 변환이나 삭제는 수행하지 않습니다.
기존 DB에 중복 이메일이 있으면 고유 인덱스 생성이 실패하므로 데이터를 정리한 후 실행해야 합니다.
Vue 프론트엔드는 `frontend`에 있으며, 개발 서버 실행 방법은 [frontend/README.md](frontend/README.md)를 참고하세요.

## 검증

```powershell
python -m pytest -q
```

각 테스트는 임시 SQLite DB를 사용하므로 기존 `db.sqlite`를 수정하지 않습니다.
가입·로그인 성공, 실패, 입력 검증, 해시 저장, JWT·쿠키, 중복 가입 경쟁,
앱 재시작 후 데이터 유지, 기존 게시판 API를 검증합니다.

## 프론트엔드

```powershell
cd frontend
npm install
npm run dev
```
