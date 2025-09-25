import json
import pytest
from unittest.mock import Mock, patch

from app.services.redis_service import (
    _get_history_key,
    save_transaction,
    check_user_cache_transaction,
    get_transaction_history_redis
)
from app.db.models import Transaction
from app.api.schemas.banking import  TransactionHistory

@pytest.mark.asyncio
async def test_get_history_key():
    result = _get_history_key(1, "main_account")
    assert result == f"user:{1}:history:main_account"

@pytest.mark.asyncio
async def test_get_history_key_diff_users():
    key1 = _get_history_key(1, "account")
    key2 = _get_history_key(2, "account")
    assert key1 != key2
    assert key1 == f"user:{1}:history:account"
    assert key2 == f"user:{2}:history:account"

@pytest.mark.asyncio
async def test_get_history_key_same_user_diff_account():
    key1 = _get_history_key(1, "first_account")
    key2 = _get_history_key(1, "second_account")
    assert key1 != key2

@pytest.mark.asyncio
async def test_save_transaction_success():
    history_mock = Mock(spec=Transaction)
    history_mock.description = "Пополнение счета"
    history_mock.amount = 100
    history_mock.from_account_id = None
    history_mock.user_id = 1

    mock_redis = Mock()
    mock_redis.rpush = Mock()
    mock_redis.ltrim = Mock()
    mock_redis.expire = Mock()

    with patch("app.services.redis_service.get_redis", return_value=mock_redis), \
    patch("app.services.redis_service._get_history_key", return_value="user:1:history:first_account"):
        save_transaction(history_mock, "first_account")
        mock_redis.rpush.assert_called_once()
        mock_redis.ltrim.assert_called_once_with("user:1:history:first_account", start=-10, end=-1)
        mock_redis.expire.assert_called_once_with(name="user:1:history:first_account", time=3600)

@pytest.mark.asyncio
async def test_save_transaction_execption():
    history_mock = Mock(spec=Transaction)
    history_mock.description = "Пополнение счета"
    history_mock.amount = 100
    history_mock.from_account_id = None
    history_mock.user_id = 1

    mock_redis = Mock()
    json_error = json.JSONDecodeError("Error", "doc", 0)
    mock_redis.rpush.side_effect = json_error
    with patch("app.services.redis_service.get_redis", return_value=mock_redis), \
    patch("app.services.redis_service._get_history_key", return_value="user:1:history:first_account"), \
    patch("app.services.redis_service.logger") as mock_logger:
        save_transaction(history_mock, "first_account")
        mock_logger.error.assert_called_once_with(
            "Ошибка сериализации транзакции для счета '%s': %s",
            "first_account",
            json_error
        )

@pytest.mark.asyncio
async def test_check_user_cache_transaction_key_exist():
    mock_redis = Mock()
    mock_redis.exists.return_value = True
    with patch("app.services.redis_service.get_redis", return_value=mock_redis), \
    patch("app.services.redis_service._get_history_key"):
        result = check_user_cache_transaction(1, "first_account")
        assert result == True

@pytest.mark.asyncio
async def test_check_user_cache_transaction_key_not_exist():
    mock_redis = Mock()
    mock_redis.exists.return_value = False
    with patch("app.services.redis_service.get_redis", return_value=mock_redis), \
    patch("app.services.redis_service._get_history_key"):
        result = check_user_cache_transaction(1, "first_account")
        assert result == False

@pytest.mark.asyncio
async def test_get_transaction_history_redis():
    mock_redis = Mock()
    history_data = [
        {"description": "Пополнение счета", "amount": "+500"}, {"description": "Перевод со счета f на s", "amount": "-15500"}
    ]
    mock_redis.lrange.return_value = [json.dumps(x).encode() for x in history_data]
    with patch("app.services.redis_service.get_redis", return_value=mock_redis), \
        patch("app.services.redis_service._get_history_key"):
        result = get_transaction_history_redis(1, "first_account")
        assert len(result) == 2
        assert type(result[0]) == TransactionHistory