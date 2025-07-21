from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from app.db.database import get_db
from app.api.schemas.users import Token, SignUp, UserOut
from app.services.users import sign_up_user_services

user_router = APIRouter(prefix="/users", tags=["User"])

@user_router.post('/login')
async def login(user_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]) -> Token:
    user = await authenticate_user(user_data.username, user_data.password, db)
    access_token = await create_access_token({"sub": user.username}, expire_time=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=access_token, token_type="Bearer")

@user_router.post("/register")
async def sign_up_user(user_data: SignUp, db: Annotated[AsyncSession, Depends(get_db)]):
    await sign_up_user_services(user_data=user_data, session=db)
    return {"message": "User successfuly created"}