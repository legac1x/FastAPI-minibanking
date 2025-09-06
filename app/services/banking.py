from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload

from app.db.models import User, Account, Transaction
from app.api.schemas.banking import UserAccount, TransactionHistory
from app.api.schemas.users import UserOut
from app.core.security import get_user_from_db
from app.services.redis_service import save_transaction, check_user_cache_transaction, get_transaction_history_redis

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

async def get_account(acc_name: str, session: AsyncSession, user_id: int) -> Account:
    query_account = await session.execute(select(Account).where(Account.name == acc_name, Account.user_id == user_id))
    account = query_account.scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account name"
        )
    return account

async def get_certain_account_service(account_name: str, session: AsyncSession, user_id: int) -> UserAccount:
    account = await get_account(acc_name=account_name, session=session, user_id=user_id)
    return UserAccount(account_name=account.name, balance=account.balance, created_at=account.created_at)

async def get_all_accounts_service(username: str, session: AsyncSession) -> List[UserAccount]:
    query_user = await session.execute(select(User).where(User.username == username).options(selectinload(User.accounts)))
    user = query_user.scalar()
    accounts = []
    for acc in user.accounts:
        accounts.append(UserAccount(
            account_name=acc.name,
            balance=acc.balance,
            created_at=acc.created_at
        ))
    return accounts

async def deposit_account_balance_service(
    account_name: str,
    amount: float,
    session: AsyncSession,
    user_id: int
) -> None:

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero"
        )

    account = await get_account(acc_name=account_name, session=session, user_id=user_id)
    history_transaction = Transaction(
        from_account=None,
        to_account=account,
        amount=amount,
        description=f"Пополнение счета {account_name}",
        user_id=user_id
    )
    save_transaction(history_transaction=history_transaction, acc_name=account_name)
    session.add(history_transaction)
    account.balance += amount
    await session.commit()

async def transfer_money_service(
    account_name: str,
    amount: float,
    session: AsyncSession,
    user_id: int,
    transfer_account_name: str,
    transfer_username: str | None = None,
) -> None:
    if transfer_account_name is None:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter transfer account name"
            )
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero"
        )

    account = await get_account(acc_name=account_name, session=session, user_id=user_id)
    if amount > account.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There are insufficient funds in the account"
        )
    
    if transfer_username is None:
        transfer_account = await get_account(acc_name=transfer_account_name, session=session, user_id=user_id)
    else:
        to_user = await get_user_from_db(username=transfer_username, session=session)
        transfer_account = await get_account(acc_name=transfer_account_name, session=session, user_id=to_user.id)

    history_transaction = Transaction(
        from_account=account,
        to_account=transfer_account,
        amount=amount,
        description=f"Перевод со счета {account_name} на {transfer_account_name}",
        user_id=user_id
    )
    save_transaction(history_transaction=history_transaction, acc_name=account_name)
    session.add(history_transaction)
    account.balance -= amount
    transfer_account.balance += amount
    await session.commit()

async def get_transaction_hisotry_service(user_data: UserOut, account_name: str, session: AsyncSession):
    user = await get_user_from_db(username=user_data.username, session=session)
    if check_user_cache_transaction(user_id=user.id, acc_name=account_name):
        result = get_transaction_history_redis(user_id=user.id, acc_name=account_name)
    else:
        account = await get_account(acc_name=account_name, session=session, user_id=user.id)
        history_query = await session.execute(select(Transaction).where(
            or_(and_(Transaction.from_account_id == None, Transaction.to_account_id == account.id),
                (Transaction.from_account_id == account.id))
        ))
        history = history_query.scalars().all()
        result = []
        for h in history:
            save_transaction(history_transaction=h, acc_name=account_name)
            result.append(
                TransactionHistory(
                    description=h.description,
                    amount=f"{"+" if h.from_account_id is None else "-"}{h.amount}"
                )
            )
    return result

async def delete_account_service(account_name: str, session: AsyncSession, user_id: int):
    account = await get_account(acc_name=account_name, session=session, user_id=user_id)
    await session.delete(account)
    await session.commit()