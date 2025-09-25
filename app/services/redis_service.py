import json

from app.core.redis import get_redis
from app.api.schemas.banking import TransactionHistory
from app.db.models import Transaction

from app.core.logging import logger

def _get_history_key(user_id: int, acc_name: str):
    logger.debug("Получение ключа для кеша транзакций счета '%s'", acc_name)
    return f"user:{user_id}:history:{acc_name}"

def save_transaction(history_transaction: Transaction, acc_name: str):
    try:
        logger.info("Сохранение транзакций счета '%s' в кеш", acc_name)
        history_pydantic = TransactionHistory(
            description=history_transaction.description,
            amount=f"{"+" if history_transaction.from_account_id is None else "-"}{history_transaction.amount}"
        )
        redis = get_redis()
        key = _get_history_key(user_id=history_transaction.user_id, acc_name=acc_name)
        logger.debug("Добавление транзакции счета '%s' в очередь", acc_name)
        redis.rpush(key, history_pydantic.model_dump_json())
        redis.ltrim(key, start=-10, end=-1)
        redis.expire(name=key, time=60*60)
    except json.JSONDecodeError as e:
        logger.error("Ошибка сериализации транзакции для счета '%s': %s", acc_name, e)

def check_user_cache_transaction(user_id: int, acc_name: str):
    logger.debug("Проверка кеша транзакций счета '%s' пользователя", acc_name)
    redis = get_redis()
    key = _get_history_key(user_id=user_id, acc_name=acc_name)
    exists = redis.exists(key)
    logger.debug("Кеш для счета '%s' %s", acc_name, "существует" if exists else "не найден")
    return exists

def get_transaction_history_redis(user_id: int, acc_name: str):
    logger.info("Получение кеша транзакций со счета '%s'", acc_name)
    history = []
    redis = get_redis()
    key = _get_history_key(user_id=user_id, acc_name=acc_name)
    cache = redis.lrange(name=key, start=0, end=-1)
    logger.debug("Формирование списка последних транзакций счета '%s'", acc_name)
    for h in cache:
        history.append(TransactionHistory(**json.loads(h.decode())))
    logger.info("Возврат %d транзакций из кеша для счета '%s' пользователю", len(history), acc_name)
    return history
