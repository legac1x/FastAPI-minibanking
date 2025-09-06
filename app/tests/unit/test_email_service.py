import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime,timedelta

from app.db.models import User
from app.services.email import (
    send_email_verification_code,
    verify_user_code
)

@pytest.mark.asyncio
async def test_send_email_verification_code():
    mock_session = AsyncMock()
    fake_user = User(
        first_name="Test",
        last_name="Test",
        username="test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=False,
    )

    with patch("app.services.email.send_email.delay") as mock_send_email:
        await send_email_verification_code(user=fake_user, session=mock_session)

        mock_session.commit.assert_awaited_once()

        mock_send_email.assert_called_once()
        args = mock_send_email.call_args[0]
        assert args[0] == "test@gmail.com"
        assert 100000 <= args[1] <= 999999

        assert isinstance(fake_user.email_verification_code, int)

@pytest.mark.asyncio
async def test_verify_user_code_return_true():
    mock_session = AsyncMock()
    fake_user = User(
        first_name="Test",
        last_name="Test",
        username="test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=False,
        email_verification_code=123456,
        email_verification_code_expires=datetime.now() + timedelta(minutes=15)
    )

    user_query = MagicMock()
    user_query.scalar_one_or_none.return_value = fake_user

    mock_session.execute.return_value = user_query

    result = await verify_user_code(user_code=123456, email="test@gmail.com", session=mock_session)

    assert result is True
    mock_session.commit.assert_awaited_once()
    assert fake_user.is_email_verified == True
    assert fake_user.email_verification_code == None
    assert fake_user.email_verification_code_expires == None

@pytest.mark.asyncio
async def test_verify_user_code_return_false():
    mock_session = AsyncMock()
    fake_user = User(
        first_name="Test",
        last_name="Test",
        username="test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=False,
        email_verification_code=123456,
        email_verification_code_expires=datetime.now() + timedelta(minutes=15)
    )

    user_query = MagicMock()
    user_query.scalar_one_or_none.return_value = fake_user
    mock_session.execute.return_value = user_query
    wrong_code = await verify_user_code(user_code=654321, email="test@gmail.com", session=mock_session)
    assert wrong_code is False

    fake_user.email_verification_code_expires = datetime.now() - timedelta(minutes=5)
    user_query = MagicMock()
    user_query.scalar_one_or_none.return_value = fake_user
    mock_session.execute.return_value = user_query
    wrong_time = await verify_user_code(user_code=123456, email="test@gmail.com", session=mock_session)
    assert wrong_time is False

    user_query = MagicMock()
    user_query.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = user_query
    user_not_found = await verify_user_code(user_code=123456, email="test@gmail.com", session=mock_session)
    assert user_not_found is False
