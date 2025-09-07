from fastapi import FastAPI
from app.core.logging import setup_logging
from app.routers import health, prompts, runs, evals

logger = setup_logging()

def create_app() -> FastAPI:
    app = FastAPI(title="Sparkling API", version="0.1.0")
    app.include_router(health.router)
    app.include_router(prompts.router)
    app.include_router(runs.router)
    app.include_router(evals.router)
    return app

app = create_app()
