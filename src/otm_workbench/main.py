from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from otm_workbench.config import get_settings
from otm_workbench.database import session_scope
from otm_workbench.platform.routes import router as platform_router
from otm_workbench.reference.routes import router as reference_router
import otm_workbench.models  # noqa: F401


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OTM Workbench", version="0.1.0")
    app.include_router(platform_router)
    app.include_router(reference_router)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            payload = {
                "code": detail["code"],
                "message": detail["message"],
                "details": detail.get("details", {}),
            }
        elif exc.status_code == 404:
            payload = {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
                "details": {},
            }
        else:
            payload = {"code": "HTTP_ERROR", "message": str(detail), "details": {}}
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "The request payload is invalid.",
                "details": {"errors": exc.errors()},
            },
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        database_status = "ok"
        try:
            with session_scope() as session:
                session.execute(text("select 1"))
        except Exception:
            database_status = "error"
        return {
            "status": "ok" if database_status == "ok" else "degraded",
            "service": settings.service_name,
            "database": database_status,
        }

    return app


app = create_app()
