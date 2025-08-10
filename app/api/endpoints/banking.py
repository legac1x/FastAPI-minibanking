from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.core.security import get_current_user, get_user_from_db
from app.db.database import get_db
from app.api.schemas.users import UserOut
from app.api.schemas.banking import UserAccount, TransferDataBalance, DepositeAccountBalance
from app.services.banking import (
    add_account_service,
    get_all_accounts_service,
    get_certain_account_service,
    transfer_money_service,
    delete_account_service,
    deposit_account_balance_service
)


banking_router = APIRouter(prefix="/banking", tags=["Bank operations"], dependencies=[Depends(get_current_user)])

@banking_router.post("/add/account")
async def add_new_account(
    account_name: str,
    user_data: Annotated[UserOut, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    await add_account_service(account_name=account_name, username=user_data.username, session=db)
    return {"message": "New account was successfully created"}

@banking_router.get('/account/{account_name}')
async def get_certain_account(
    account_name: str,
    user: Annotated[UserOut, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserAccount:
    user = await get_user_from_db(user.username, session=db)
    return await get_certain_account_service(account_name=account_name, session=db, user_id=user.id)

@banking_router.get('/accounts')
async def get_all_accounts(
    user_data: Annotated[UserOut, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    res = await get_all_accounts_service(username=user_data.username, session=db)
    return {"username": user_data.username, "Accounts": res}

@banking_router.post('/change/transfer')
async def transfer_money(
    transfer_data: TransferDataBalance,
    user: Annotated[UserOut, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    user = await get_user_from_db(user.username, session=db)
    await transfer_money_service(
        account_name=transfer_data.account_name,
        amount=transfer_data.amount,
        session=db,
        user_id=user.id,
        transfer_account_name=transfer_data.transfer_account_name,
        transfer_username=transfer_data.transfer_username,
    )
    return {"message": "The money was successfully transferred"}

@banking_router.post("/change/deposit")
async def deposit_account_balance(
    deposit_account_data: DepositeAccountBalance,
    user: Annotated[UserOut, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await get_user_from_db(user.username, session=db)
    await deposit_account_balance_service(
        account_name=deposit_account_data.account_name,
        amount=deposit_account_data.amount,
        session=db,
        user_id=user.id
    )
    return {"message": "Account has been successfully replenished"}

@banking_router.delete('/delete')
async def delete_account(
    account_name: str,
    user: Annotated[UserOut, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await get_user_from_db(user.username, session=db)
    await delete_account_service(account_name=account_name, session=db, user_id=user.id)
    return {"message": "The bank account was successfully deleted"}