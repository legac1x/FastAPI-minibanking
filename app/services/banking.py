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
from app.core.logging import logger

async def add_account_service(account_name: str, username: str, session: AsyncSession):
    logger.debug("Проверка существования счета с именем '%s'", account_name)
    query_account = await session.execute(select(Account).where(Account.name == account_name))
    account = query_account.scalar_one_or_none()
    if not account:
        logger.info("Счет с именем '%s' не найден. Создание нового счета для '%s'", account_name, username)
        query_user = await session.execute(select(User).where(User.username == username))
        user = query_user.scalar()
        new_account = Account(
            name=account_name,
            user=user
        )
        session.add(new_account)
        await session.commit()
        logger.info("Успешно создан счет '%s' для пользователя '%s'", account_name, username)
    else:
        logger.warning("Попытка создать существующий акаунт '%s'", account_name)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account name is already used"
        )

async def get_account(acc_name: str, session: AsyncSession, user_id: int) -> Account:
    logger.debug("Поиск счета '%s' для пользователя '%s'", acc_name, user_id)
    query_account = await session.execute(select(Account).where(Account.name == acc_name, Account.user_id == user_id))
    account = query_account.scalar_one_or_none()
    if account is None:
        logger.warning("Пользователь '%s' пытается получить доступ к несуществующему счету '%s'", user_id, acc_name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account name"
        )
    logger.debug("Счет '%s' успешно найден для пользователя '%s'", acc_name, user_id)
    return account

async def get_certain_account_service(account_name: str, session: AsyncSession, user_id: int) -> UserAccount:
    account = await get_account(acc_name=account_name, session=session, user_id=user_id)
    logger.info("Возврат счета '%s' пользователю", account_name)
    return UserAccount(account_name=account.name, balance=account.balance, created_at=account.created_at)

async def get_all_accounts_service(username: str, session: AsyncSession) -> List[UserAccount]:
    query_user = await session.execute(select(User).where(User.username == username).options(selectinload(User.accounts)))
    user = query_user.scalar()
    accounts = []
    logger.debug("Поиск всех счетов пользователя '%s'", username)
    for acc in user.accounts:
        accounts.append(UserAccount(
            account_name=acc.name,
            balance=acc.balance,
            created_at=acc.created_at
        ))
    logger.info("Возврат всех счетов для пользователя '%s'", username)
    return accounts

async def deposit_account_balance_service(
    account_name: str,
    amount: float,
    session: AsyncSession,
    user_id: int
) -> None:
    logger.info("Пополнение счета '%s' на сумму %.2f", account_name, amount)
    if amount <= 0:
        logger.warning("Некорректная сумма пополнения: '%s'", amount)
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
    logger.debug("Сохранение транзакции в кеш и БД")
    save_transaction(history_transaction=history_transaction, acc_name=account_name)
    session.add(history_transaction)
    account.balance += amount
    logger.info("Успешное пополнение счета '%s' на %.2f", account_name, amount)
    await session.commit()

async def transfer_money_service(
    account_name: str,
    amount: float,
    session: AsyncSession,
    user_id: int,
    transfer_account_name: str,
    transfer_username: str | None = None,
) -> None:
    logger.info("Перевод средств со счета '%s' на '%s'", account_name, transfer_account_name)

    if amount <= 0:
        logger.warning("Некорректная сумма перевода: %.2f", amount)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero"
        )

    account = await get_account(acc_name=account_name, session=session, user_id=user_id)
    if amount > account.balance:
        logger.warning("Введенная сумма превышает баланс пользователя. Запрошено %.2f, доступно %.2f", amount, account.balance)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There are insufficient funds in the account"
        )
    logger.debug("Перевод между своими счетами или другому пользователю")
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
    logger.debug("Сохранение транзакции в кеш и БД")
    save_transaction(history_transaction=history_transaction, acc_name=account_name)
    session.add(history_transaction)
    account.balance -= amount
    transfer_account.balance += amount
    logger.info("Успешный перевод %.2f со счета '%s' на '%s'", amount, account_name, transfer_account_name)
    await session.commit()

async def get_transaction_hisotry_service(user_data: UserOut, account_name: str, session: AsyncSession):
    user = await get_user_from_db(username=user_data.username, session=session)
    if check_user_cache_transaction(user_id=user.id, acc_name=account_name):
        logger.debug("Получение списка транзакций счета '%s' из кеша редис", account_name)
        result = get_transaction_history_redis(user_id=user.id, acc_name=account_name)
    else:
        logger.debug("Получение списка транзакций счета '%s' из БД", account_name)
        account = await get_account(acc_name=account_name, session=session, user_id=user.id)
        history_query = await session.execute(select(Transaction).where(
            or_(and_(Transaction.from_account_id == None, Transaction.to_account_id == account.id),
                (Transaction.from_account_id == account.id))
        ))
        history = history_query.scalars().all()
        result = []
        logger.debug("Формирование списка из %d транзакций и запись в кеш", len(history))
        for h in history:
            save_transaction(history_transaction=h, acc_name=account_name)
            result.append(
                TransactionHistory(
                    description=h.description,
                    amount=f"{"+" if h.from_account_id is None else "-"}{h.amount}"
                )
            )
    logger.info("Возврат %d транзакций счета '%s' пользователю '%s'", len(result), account_name, user_data.username)
    return result

async def delete_account_service(account_name: str, session: AsyncSession, user_id: int):
    account = await get_account(acc_name=account_name, session=session, user_id=user_id)
    logger.info("Удаление счета '%s' для пользователя '%s'", account_name, account.user.username)
    await session.delete(account)
    await session.commit()