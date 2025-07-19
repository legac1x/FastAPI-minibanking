from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.database import get_db
from app.api.schemas.users import Token

user_router = APIRouter(prefix="/users", tags=["User"])

@user_router('/users/login', response_model=Token)
async def login(user_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]) -> Token:
    user = await authenticate_user(user_data.username, user_data.password, db)
    access_token = await create_access_token({"sub": user.username}, expire_time=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=access_token, token_type="Bearer")