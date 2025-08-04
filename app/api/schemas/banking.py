from datetime import datetime

from pydantic import BaseModel

class UserAccount(BaseModel):
    account_name: str
    balance: float
    created_at: datetime

class DepositeAccountBalance(BaseModel):
    account_name: str
    amount: float

class TransferDataBalance(BaseModel):
    account_name: str
    amount: float
    transfer_username: str | None = None
    transfer_account_name: str
