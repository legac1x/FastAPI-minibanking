import json

from app.core.redis import get_redis
from app.api.schemas.banking import TransactionHistory
from app.db.models import Transaction

def _get_history_key(user_id: int, acc_name: str):
    return f"user:{user_id}:history:{acc_name}"

def save_transaction(history_transaction: Transaction, acc_name: str):
    history_pydantic = TransactionHistory(
        description=history_transaction.description,
        amount=f"{"+" if history_transaction.from_account_id is None else "-"}{history_transaction.amount}"
    )
    redis = get_redis()
    key = _get_history_key(user_id=history_transaction.user_id, acc_name=acc_name)
    redis.rpush(key, history_pydantic.model_dump_json())
    redis.ltrim(key, start=-10, end=-1)
    redis.expire(name=key, time=60*60)

def check_user_cache_transaction(user_id: int, acc_name: str):
    redis = get_redis()
    key = _get_history_key(user_id=user_id, acc_name=acc_name)
    return redis.exists(key)

def get_transaction_history_redis(user_id: int, acc_name: str):
    history = []
    redis = get_redis()
    key = _get_history_key(user_id=user_id, acc_name=acc_name)
    cache = redis.lrange(name=key, start=0, end=-1)
    for h in cache:
        history.append(TransactionHistory(**json.loads(h.decode())))
    return history
