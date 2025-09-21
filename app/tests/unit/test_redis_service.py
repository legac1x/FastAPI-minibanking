import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.redis_service import _get_history_key

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