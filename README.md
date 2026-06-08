# QA Console Gateway

FastAPI 기반 통합 Gateway입니다. 사용자는 이 콘솔에 한 번 로그인한 뒤 상단 탭으로 기존 Render 서비스 2개를 전환해서 사용할 수 있습니다.

## 대상 서비스

- 결함 회귀 테스트: `https://regression-gohanpass-web.onrender.com`
- 웹 자동 검증: `https://gohanpass-web-validator.onrender.com`

기존 두 서비스의 Backend, URL, API, 실행 방식은 수정하지 않습니다. 이 프로젝트는 통합 진입점, 공통 로그인, 탭 UI만 제공합니다.

## 로컬 실행

```bash
cd gohanpass-qa-console
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
SESSION_SECRET=local-dev-secret uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

브라우저에서 `http://127.0.0.1:8000`으로 접속합니다.

기본 계정은 `qa / qa`입니다.

## 환경변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `QA_CONSOLE_USER` | `qa` | Gateway 로그인 ID |
| `QA_CONSOLE_PASSWORD` | `qa` | Gateway 로그인 비밀번호 |
| `SESSION_SECRET` | 없음 | signed cookie 서명 키 |
| `REGRESSION_APP_URL` | `https://regression-gohanpass-web.onrender.com` | 결함 회귀 테스트 iframe URL |
| `VALIDATOR_APP_URL` | `https://gohanpass-web-validator.onrender.com` | 웹 자동 검증 iframe URL |
| `SECURE_COOKIE` | `true` | HTTPS secure cookie 사용 여부 |

운영 환경에서는 `QA_CONSOLE_USER`, `QA_CONSOLE_PASSWORD`, `SESSION_SECRET`을 반드시 환경변수로 설정하세요. `SESSION_SECRET`이 없으면 앱은 임시 secret을 생성하고 경고 로그를 출력합니다. 이 경우 프로세스 재시작 시 기존 세션은 모두 무효화됩니다.

## Render 배포

이 저장소 루트를 Render Web Service로 배포합니다. `render.yaml`, `requirements.txt`, `Dockerfile`, `app/`가 모두 루트에 있으므로 Render Blueprint가 바로 파싱할 수 있습니다.

Blueprint를 사용할 경우 `render.yaml`을 기준으로 생성합니다.

수동 생성 시:

- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Render 환경변수에서 최소 아래 값을 설정합니다.

```text
QA_CONSOLE_USER=qa
QA_CONSOLE_PASSWORD=<운영 비밀번호>
SESSION_SECRET=<충분히 긴 랜덤 문자열>
REGRESSION_APP_URL=https://regression-gohanpass-web.onrender.com
VALIDATOR_APP_URL=https://gohanpass-web-validator.onrender.com
SECURE_COOKIE=true
```

## iframe 차단 확인

대상 서비스가 아래 응답 헤더를 사용하면 Gateway iframe 안에서 표시되지 않을 수 있습니다.

- `X-Frame-Options: DENY`
- `X-Frame-Options: SAMEORIGIN`
- `Content-Security-Policy: frame-ancestors ...`

확인 방법:

```bash
curl -I https://regression-gohanpass-web.onrender.com
curl -I https://gohanpass-web-validator.onrender.com
```

브라우저 개발자 도구 Console에도 frame 차단 메시지가 표시됩니다. 이 프로젝트는 iframe 로딩 timeout 또는 error 상황에서 `새 창 열기` 버튼을 제공합니다.

## reverse proxy 전환 기준

다음 조건이면 iframe 방식만으로는 통합 UX를 안정적으로 제공하기 어렵습니다.

- 대상 서비스가 `X-Frame-Options` 또는 `frame-ancestors`로 외부 iframe 삽입을 차단하는 경우
- 하위 서비스 쿠키가 third-party cookie 정책 때문에 동작하지 않는 경우
- Gateway 로그인과 하위 서비스 인증을 하나의 SSO처럼 묶어야 하는 경우
- 탭 전환뿐 아니라 API 호출, 파일 다운로드, websocket 등을 같은 origin에서 처리해야 하는 경우

그 경우 Gateway에 서비스별 reverse proxy 라우터를 추가해 `/apps/regression/*`, `/apps/validator/*`처럼 같은 origin 경로로 전달하는 구조로 전환합니다. 현재 코드는 대상 URL을 `app/config.py`의 `ServiceConfig`로 분리해 두었으므로 proxy 라우터를 추가할 때 서비스 정의를 재사용할 수 있습니다.

## 범위

현재 범위는 통합 진입점, Gateway 로그인, 탭 UI, iframe 표시, iframe 실패 시 새 창 열기 제공까지입니다. 기존 두 서비스에 직접 접근하는 외부 사용자를 차단하지 않으며, 하위 서비스 자체 인증 통합은 후속 작업으로 분리합니다.
