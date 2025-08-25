from typing import Annotated
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.api.schemas.users import UserOut
from app.db.database import get_db
from app.db.models import User
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
ACCESS_TOKEN_EXPIRE_MINUTES = 15
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

pwd = CryptContext(schemes=['bcrypt'], deprecated="auto")

async def get_user_from_db(username: str, session: AsyncSession) ->  User:
    query = await session.execute(select(User).where(User.username == username))
    user = query.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User wasn't found."
        )
    return user

def get_hashed_password(password: str):
    return pwd.hash(password)

def verify_password(user_password: str, hash_password: str):
    return pwd.verify(user_password, hash_password)

async def authenticate_user(username: str, password: str, session: AsyncSession) -> User:
    user = await get_user_from_db(username, session)
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Check your email."
        )
    return user

async def create_access_token(data: dict, expire_time: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expire_time:
        expire = datetime.now(timezone.utc) + expire_time
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    access_token = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return access_token

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[AsyncSession, Depends(get_db)]) -> UserOut:
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        user = await get_user_from_db(username, db)
        return UserOut(
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )