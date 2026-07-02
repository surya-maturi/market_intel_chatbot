import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import chat, health
from app.config import get_settings
from app.db.session import init_db
from app.logging_conf import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    init_db()
    logging.getLogger(__name__).info("Service status: %s", settings.service_status)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Market Intel Chatbot", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
