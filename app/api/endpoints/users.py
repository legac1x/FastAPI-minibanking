from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.database import get_db
from app.api.schemas.users import Token, SignUp, EmailVerificationRequest
from app.services.users import sign_up_user_services
from app.services.email import verify_user_code
from app.core.logging import logger

user_router = APIRouter(prefix="/users", tags=["User"])

@user_router.post('/login')
async def login(user_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]) -> Token:
    logger.info("Авторизация пользователя '%s'", user_data.username)
    user = await authenticate_user(user_data.username, user_data.password, db)
    access_token = await create_access_token({"sub": user.username}, expire_time=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    logger.info("Возврат JWT токена пользователю '%s'", user_data.username)
    return Token(access_token=access_token, token_type="Bearer")

@user_router.post("/register")
async def sign_up_user(user_data: SignUp, db: Annotated[AsyncSession, Depends(get_db)]):
    logger.info("Регистрация пользователя '%s' с почтой '%s'", user_data.username, user_data.email)
    await sign_up_user_services(user_data=user_data, session=db)
    return {"message": "User successfuly created"}

@user_router.post("/verified")
async def verified_user(email_data: EmailVerificationRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    logger.info("Верификация пользователя по электронной почте")
    is_verified = await verify_user_code(user_code=email_data.code, email=email_data.email, session=db)
    if is_verified:
        logger.debug("Пользователь успешно прошел верификацию")
        return {"Message": "Email successfully verified!"}
    else:
        logger.warning("Введенный пользователем код неверный либо его время истекло")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code or code expired"
        )