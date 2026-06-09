import logging
from urllib.parse import urlencode

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import attach_session, clear_session, get_current_user, verify_credentials
from app.config import ServiceConfig, get_settings
from app.sso import create_service_token


logging.basicConfig(level=logging.INFO)

settings = get_settings()
app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _redirect_to_login() -> RedirectResponse:
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


def _service_by_key(service_key: str) -> ServiceConfig | None:
    return next((service for service in settings.services if service.key == service_key), None)


def _build_launch_url(user: str, service: ServiceConfig) -> tuple[str, int]:
    if settings.shared_secret:
        token, expires_at = create_service_token(user, service, settings)
        query = urlencode({"qa_console_token": token})
        return f"{service.launch_url}?{query}", expires_at
    return service.url, 0


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Response:
    user = get_current_user(request, settings)
    if not user:
        return _redirect_to_login()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "user": user,
            "services": settings.services,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request) -> Response:
    if get_current_user(request, settings):
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "error": None,
        },
    )


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
) -> Response:
    if not verify_credentials(username, password, settings):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "error": "아이디 또는 비밀번호가 올바르지 않습니다.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    attach_session(response, username, settings)
    return response


@app.post("/logout")
async def logout(request: Request) -> HTMLResponse:
    response = templates.TemplateResponse(
        "logout.html",
        {
            "request": request,
            "logout_urls": [service.logout_url for service in settings.services],
        },
        status_code=status.HTTP_200_OK,
    )
    clear_session(response)
    return response


@app.get("/api/services/{service_key}/launch")
async def service_launch(service_key: str, request: Request) -> dict[str, str | int]:
    user = get_current_user(request, settings)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="login required")

    service = _service_by_key(service_key)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="service not found")

    launch_url, expires_at = _build_launch_url(user, service)
    return {
        "serviceKey": service.key,
        "launchUrl": launch_url,
        "externalUrl": launch_url,
        "baseUrl": service.url,
        "expiresAt": expires_at,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "qa-console-gateway"}
