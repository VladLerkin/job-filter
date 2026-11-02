"""Инициализация приложения FastAPI, мидлварей, CORS и подключение роутеров."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from job_filter import config
from job_filter.api.routers import blacklist, candidate, hirify, jobs, pipeline, skills, ui
from job_filter.db.connection import init_db
from job_filter.logging_setup import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Job Filter", lifespan=lifespan)

    if config.STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def allow_private_network_middleware(request: Request, call_next):
        if request.method == "OPTIONS" and request.headers.get("access-control-request-private-network") == "true":
            resp = Response(status_code=204)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "*"
            resp.headers["Access-Control-Allow-Headers"] = "*"
            resp.headers["Access-Control-Allow-Private-Network"] = "true"
            return resp
        response = await call_next(request)
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    app.include_router(ui.router)
    app.include_router(pipeline.router)
    app.include_router(jobs.router)
    app.include_router(skills.router)
    app.include_router(candidate.router)
    app.include_router(blacklist.router)
    app.include_router(hirify.router)

    return app


app = create_app()
