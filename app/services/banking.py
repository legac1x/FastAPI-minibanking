from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import User, Account

async def add_account_service(account_name: str, username: str, session: AsyncSession):
    query_account = await session.execute(select(Account).where(Account.name == account_name))
    account = query_account.scalar_one_or_none()
    if not account:
        query_user = await session.execute(select(User).where(User.username == username))
        user = query_user.scalar()
        new_account = Account(
            name=account_name,
            user=user
        )
        session.add(new_account)
        await session.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account name is already used"
        )