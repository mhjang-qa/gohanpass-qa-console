import logging
import os
import secrets
from dataclasses import dataclass
from urllib.parse import urljoin


LOGGER = logging.getLogger("qa_console_gateway")


@dataclass(frozen=True)
class ServiceConfig:
    key: str
    name: str
    description: str
    url: str
    target: str

    @property
    def launch_url(self) -> str:
        return urljoin(f"{self.url.rstrip('/')}/", "sso/launch")

    @property
    def logout_url(self) -> str:
        return urljoin(f"{self.url.rstrip('/')}/", "sso/logout")


@dataclass(frozen=True)
class Settings:
    app_name: str
    console_user: str
    console_password: str
    session_secret: str
    shared_secret: str
    token_expire_minutes: int
    secure_cookie: bool
    services: tuple[ServiceConfig, ...]


def _read_session_secret() -> str:
    secret = os.getenv("SESSION_SECRET", "")
    if secret:
        return secret

    LOGGER.warning(
        "SESSION_SECRET is not set. An ephemeral development secret was generated; "
        "all sessions will be invalidated when the process restarts."
    )
    return secrets.token_urlsafe(48)


def _read_shared_secret() -> str:
    secret = os.getenv("QA_CONSOLE_SHARED_SECRET", "").strip()
    if secret:
        return secret

    LOGGER.warning(
        "QA_CONSOLE_SHARED_SECRET is not set. Console SSO launch tokens are disabled "
        "until a shared secret is configured in the console and child services."
    )
    return ""


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("QA_CONSOLE_NAME", "GO Hanpass QA Console"),
        console_user=os.getenv("QA_CONSOLE_USER", "qa"),
        console_password=os.getenv("QA_CONSOLE_PASSWORD", "qa"),
        session_secret=_read_session_secret(),
        shared_secret=_read_shared_secret(),
        token_expire_minutes=max(1, int(os.getenv("QA_CONSOLE_TOKEN_EXPIRE_MINUTES", "10"))),
        secure_cookie=os.getenv("SECURE_COOKIE", "true").lower() in {"1", "true", "yes", "on"},
        services=(
            ServiceConfig(
                key="regression",
                name="결함 회귀 테스트",
                description="Notion 결함 DB 기반 재현 단계 분석 및 회귀 테스트 실행",
                url=os.getenv(
                    "REGRESSION_APP_URL",
                    "https://regression-gohanpass-web.onrender.com",
                ),
                target="regression",
            ),
            ServiceConfig(
                key="validator",
                name="웹 자동 검증",
                description="GO Hanpass 웹 시나리오 자동 실행 및 결과 리포트 생성",
                url=os.getenv(
                    "VALIDATOR_APP_URL",
                    "https://gohanpass-web-validator.onrender.com",
                ),
                target="validator",
            ),
        ),
    )
