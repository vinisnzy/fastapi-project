from fastapi import FastAPI
from fastapi_pagination import add_pagination

from fastapi_project.exceptions.error_handlers import register_error_handlers
from fastapi_project.routers import jokes

app = FastAPI()

register_error_handlers(app)
app.include_router(jokes.router)
add_pagination(app)


@app.get("/")
def read_root() -> dict:
    return {"message": "Welcome to the joke API!"}
