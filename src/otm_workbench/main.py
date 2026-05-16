from fastapi import FastAPI

from otm_workbench.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OTM Workbench", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "database": "not_configured",
        }

    return app


app = create_app()
