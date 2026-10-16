# 모아 노트 웹 페이지

순수 HTML, CSS, JavaScript로 구현했습니다.

## 실행 및 배포

app/web 폴더의 index.html, style.css, app.js를 nginx 정적 파일 디렉터리에 배포하고 프론트엔드 주소로 접속하세요.

기본 API 경로는 /api이며 요청은 현재 페이지와 같은 호스트의 nginx로 전달됩니다.

- POST /api/user/signup
- POST /api/user/login
- POST /api/board/register
- GET /api/board/read/{idx}
- GET /api/ (연결 확인)

현재 백엔드 라우트에는 /api 접두사가 없으므로 nginx는 /api/user/login을 백엔드의 /user/login으로 전달해야 합니다. 기존 프록시가 이 경로 변환을 수행하는지 확인하세요.

서버 연결 설정은 /api 같은 루트 상대 경로 또는 HTTP(S) 절대 주소를 지원합니다. 이전 버전에 저장된 직접 연결 주소는 사용하지 않으며 새 설정은 moa-api-base-proxy-v1 키로 저장합니다. 로그인 쿠키 전송 옵션은 유지합니다.

백엔드는 기존 환경에서 python -m uvicorn app.main:app --reload로 실행할 수 있습니다. 페이지는 nginx 주소로 열어야 기본 /api 프록시를 이용합니다. 목록 API가 없으므로 저장된 노트 번호를 기록해 두세요.

## 기존 백엔드 확인 사항

user.py의 login은 비밀번호가 틀려도 기존 user 객체를 반환할 수 있습니다. 프런트엔드에서는 실제 인증 성공 여부를 구분할 수 없으므로 백엔드에서 인증 실패 시 401을 반환하도록 수정해야 합니다. 없는 사용자 로그인이나 없는 노트 조회는 None 반환으로 500 오류가 발생할 수 있습니다. 이번 작업에서는 기존 API 로직을 변경하지 않았습니다.

## 검증

JS 구문, DOM 참조, 모의 API 주소/쿠키 옵션, 안전한 텍스트 표시 및 422 오류 처리를 확인했습니다. 실제 서버/DB 연동 및 브라우저 시각 검증은 수행하지 않았습니다.
