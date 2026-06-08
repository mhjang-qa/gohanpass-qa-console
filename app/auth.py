from itsdangerous import BadSignature, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import Response

from app.config import Settings


SESSION_COOKIE = "qa_console_session"
SESSION_SALT = "qa-console-session-v1"


def _serializer(settings: Settings) -> URLSafeSerializer:
    return URLSafeSerializer(settings.session_secret, salt=SESSION_SALT)


def get_current_user(request: Request, settings: Settings) -> str | None:
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie:
        return None

    try:
        payload = _serializer(settings).loads(cookie)
    except BadSignature:
        return None

    username = payload.get("user") if isinstance(payload, dict) else None
    if username != settings.console_user:
        return None
    return username


def verify_credentials(username: str, password: str, settings: Settings) -> bool:
    return username == settings.console_user and password == settings.console_password


def attach_session(response: Response, username: str, settings: Settings) -> None:
    token = _serializer(settings).dumps({"user": username})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        max_age=60 * 60 * 12,
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
