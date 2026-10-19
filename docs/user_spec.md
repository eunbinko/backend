# 회원 가입 및 로그인 기능 용구사항 명세

## API
- POST /user/signup
- POST /user/login


## 입력
- email
- passord
- name

##
- code 상태 코드
- result 결과

## 예외
- 이메일 중복 409
- 이메일 또는 비밀번호 틀림 401

## 제외
- 카카오, 구글 로그인과 같은 소셜로그인은 나중에 구현
