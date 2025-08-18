import json

from app.core.redis import get_redis
from app.api.schemas.banking import TransactionHistory
from app.db.models import Transaction

def save_transaction(history_transaction: Transaction, acc_name: str):
    history_pydantic = TransactionHistory(
        description=history_transaction.description,
        amount=f"{"+" if history_transaction.from_account_id is None else "-"}{history_transaction.amount}"
    )
    redis = get_redis()

    if redis.exists(f"user:{history_transaction.user_id}:history:{acc_name}") and \
    redis.llen(f"user:{history_transaction.user_id}:history:{acc_name}") == 10:
        redis.lpop(f"user:{history_transaction.user_id}:history:{acc_name}")

    redis.rpush(f"user:{history_transaction.user_id}:history:{acc_name}", history_pydantic.model_dump_json())

def check_user_cache_transaction(user_id: int, acc_name: str):
    redis = get_redis()
    return redis.exists(f"user:{user_id}:history:{acc_name}")

def get_transaction_history_redis(user_id: int, acc_name: str):
    history = []
    redis = get_redis()
    cache = redis.lrange(name=f"user:{user_id}:history:{acc_name}", start=0, end=-1)
    for h in cache:
        history.append(json.loads(h.decode()))
    return history
