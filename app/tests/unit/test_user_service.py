import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.api.schemas.users import SignUp
from app.db.models import User, Account
from app.services.users import sign_up_user_services


@pytest.mark.asyncio
async def test_sign_up_user_services():
    mock_session = AsyncMock()
    hashed_password = "hashed_password123"
    with patch("app.services.users.get_hashed_password", return_value=hashed_password), \
        patch("app.services.users.send_email_verification_code") as mock_send_email:

        fake_user = SignUp(
            username="testuser",
            password="123",
            first_name="FirstName",
            last_name="LastName",
            email="test@gmail.com"
        )

        await sign_up_user_services(user_data=fake_user, session=mock_session)

        args = mock_session.add_all.call_args[0][0]
        assert len(args) == 2
        assert isinstance(args[0], User)
        assert isinstance(args[1], Account)
        mock_session.commit.assert_awaited_once()
        mock_send_email.assert_awaited_once()
