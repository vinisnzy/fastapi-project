from fastapi import FastAPI
from fastapi_pagination import add_pagination

from fastapi_project.routes import jokes

app = FastAPI()

app.include_router(jokes.router)
add_pagination(app)


@app.get("/")
def read_root() -> dict:
    return {"message": "Welcome to the joke API!"}
