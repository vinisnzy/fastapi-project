from fastapi import FastAPI

from fastapi_project.routes import jokes

app = FastAPI()

app.include_router(jokes.router)


@app.get("/")
def read_root() -> dict:
    return {"message": "Welcome to the joke API!"}
