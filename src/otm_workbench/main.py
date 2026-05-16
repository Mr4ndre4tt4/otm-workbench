from fastapi import FastAPI
from sqlalchemy import text

from otm_workbench.config import get_settings
from otm_workbench.database import session_scope
import otm_workbench.models  # noqa: F401


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OTM Workbench", version="0.1.0")

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
