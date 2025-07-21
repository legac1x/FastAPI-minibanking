from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from sqlalchemy import select

from sqlalchemy.orm import selectinload
from app.db.models import User
from app.core.security import get_current_user
from app.db.database import get_db
from app.api.schemas.users import UserOut
from app.services.banking import add_account_service

banking_router = APIRouter(prefix="/banking", tags=["Bank operations"], dependencies=[Depends(get_current_user)])

@banking_router.post("/add/account")
async def add_new_account(account_name: str, user_data: Annotated[UserOut, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    await add_account_service(account_name=account_name, username=user_data.username, session=db)
    return {"message": "New account was successfuly created"}