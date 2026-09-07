from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_project.dependencies import AuthServiceDep, CurrentUserDep
from fastapi_project.schemas.auth import RefreshRequest, TokenPair, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201, response_model=UserRead)
async def register(service: AuthServiceDep, payload: UserCreate):
    return await service.register(payload)


@router.post("/login", response_model=TokenPair)
async def login(
    service: AuthServiceDep, payload: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    return await service.login(payload.username, payload.password)


@router.post("/refresh", response_model=TokenPair)
async def refresh(service: AuthServiceDep, payload: RefreshRequest):
    return await service.refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
async def logout(service: AuthServiceDep, payload: RefreshRequest):
    await service.logout(payload.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUserDep):
    return current_user
