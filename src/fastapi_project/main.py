from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from fastapi_project.core.config import Settings, get_settings
from fastapi_project.database.session import build_engine, build_session_maker
from fastapi_project.exceptions.error_handlers import register_error_handlers
from fastapi_project.routers import jokes


def create_app(settings: Settings | None = None) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(settings or get_settings())
        session_maker = build_session_maker(engine)
        app.state.settings = settings or get_settings()
        app.state.engine = engine
        app.state.session_maker = session_maker
        yield
        await engine.dispose()

    app = FastAPI(lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(jokes.router)
    add_pagination(app)

    @app.get("/")
    def read_root() -> dict:
        return {"message": "Welcome to the joke API!"}

    return app
