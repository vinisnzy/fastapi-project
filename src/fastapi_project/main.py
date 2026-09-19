import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi_pagination import add_pagination

from fastapi_project.core.config import Settings, get_settings
from fastapi_project.core.logging import request_id_context, setup_logging
from fastapi_project.database.session import build_engine, build_session_maker
from fastapi_project.exceptions.error_handlers import (
    register_error_handlers,
    unhandled_exception_handler,
)
from fastapi_project.routers import auth, jokes

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.DEBUG)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(settings)
        session_maker = build_session_maker(engine)
        app.state.settings = settings
        app.state.engine = engine
        app.state.session_maker = session_maker
        logger.info("Application started", extra={"event": "application_started"})
        try:
            yield
        finally:
            await engine.dispose()
            logger.info("Application stopped", extra={"event": "application_stopped"})

    app = FastAPI(lifespan=lifespan)
    register_error_handlers(app)

    @app.middleware("http")
    async def correlate_request(request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        context_token = request_id_context.set(request_id)
        try:
            response = await call_next(request)
        except Exception as exc:
            response = await unhandled_exception_handler(request, exc)
        finally:
            request_id_context.reset(context_token)

        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(jokes.router)
    app.include_router(auth.router)
    add_pagination(app)

    @app.get("/")
    def read_root() -> dict:
        return {"message": "Welcome to the joke API!"}

    return app
