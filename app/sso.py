import time

from itsdangerous import BadSignature, URLSafeSerializer

from app.config import ServiceConfig, Settings


SSO_SALT = "qa-console-sso-v1"


def _serializer(settings: Settings) -> URLSafeSerializer:
    return URLSafeSerializer(settings.shared_secret, salt=SSO_SALT)


def create_service_token(user: str, service: ServiceConfig, settings: Settings) -> tuple[str, int]:
    expires_at = int(time.time()) + settings.token_expire_minutes * 60
    token = _serializer(settings).dumps(
        {
            "source": "qa-console",
            "user": user,
            "target": service.target,
            "exp": expires_at,
        }
    )
    return token, expires_at


def validate_service_token(token: str, target: str, shared_secret: str) -> dict | None:
    if not token or not shared_secret:
        return None

    try:
        payload = URLSafeSerializer(shared_secret, salt=SSO_SALT).loads(token)
    except BadSignature:
        return None

    if not isinstance(payload, dict):
        return None
    if payload.get("source") != "qa-console":
        return None
    if payload.get("target") != target:
        return None

    expires_at = int(payload.get("exp", 0))
    if expires_at <= int(time.time()):
        return None

    return payload
