from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import config, jobs, profile, runs, tailor
from app.core.config import PROJECT_ROOT

WEB_DIST_DIR = PROJECT_ROOT / "web" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Job Search Command Center",
        version="0.2.0",
        description="Local-first API for job triage, tracking, dynamic config, and AI resume tailoring.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(jobs.router)
    app.include_router(runs.router)
    app.include_router(config.router)
    app.include_router(profile.router)
    app.include_router(tailor.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    if WEB_DIST_DIR.exists() and (WEB_DIST_DIR / "index.html").exists():
        assets_dir = WEB_DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        def serve_spa(full_path: str) -> FileResponse:
            target = WEB_DIST_DIR / full_path
            if full_path and target.exists() and target.is_file():
                return FileResponse(target)
            return FileResponse(WEB_DIST_DIR / "index.html")

    return app


app = create_app()
