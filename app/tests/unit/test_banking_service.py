import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import HTTPException

from app.api.schemas.users import UserOut
from app.services.banking import (
    add_account_service,
    get_account,
    get_certain_account_service,
    get_all_accounts_service,
    deposit_account_balance_service,
    transfer_money_service,
    get_transaction_hisotry_service,
    delete_account_service
)
from app.db.models import Account, Transaction, User
from app.api.schemas.banking import TransactionHistory, UserAccount

@pytest.mark.asyncio
async def test_add_account_service_account_exists():
    mock_session = AsyncMock()

    mock_session.execute.return_value.scalar_one_or_none.return_value = True

    with pytest.raises(HTTPException) as exc:
        await add_account_service("test_account", "user1", mock_session)

    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_add_account_service_create_account():
    mock_session = AsyncMock()

    mock_query_account = MagicMock()
    mock_query_account.scalar_one_or_none.return_value = None
    mock_query_user = MagicMock()
    mock_query_user.scalar.return_value = MagicMock()

    mock_session.execute.side_effect = [mock_query_account, mock_query_user]

    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    await add_account_service("new_account", "user2", mock_session)

    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()

@pytest.mark.asyncio
async def test_get_account_not_exists():
    mock_session = AsyncMock()

    mock_query_account = MagicMock()
    mock_query_account.scalar_one_or_none.return_value = None

    mock_session.execute.side_effect = [mock_query_account]

    with pytest.raises(HTTPException) as exc:
        await get_account("account_name", mock_session, 1)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_get_account_exists():
    mock_session = AsyncMock()

    fake_account = Account(name="account_name", user_id=1, balance=5000.0, created_at=datetime.now(timezone.utc))
    mock_query_account = MagicMock()
    mock_query_account.scalar_one_or_none.return_value = fake_account

    mock_session.execute.side_effect = [mock_query_account]

    account = await get_account("account_name", mock_session, 1)

    assert account.name == "account_name"
    assert account.user_id == 1
    assert account.balance == 5000.0

@pytest.mark.asyncio
async def test_get_certain_account_service():
    mock_session = AsyncMock()

    time = datetime.now(timezone.utc)

    fake_account = Account(name="account_name", user_id=2, balance=2500.0, created_at=time)

    query_user = MagicMock()
    query_user.scalar_one_or_none.return_value = fake_account
    mock_session.execute.side_effect = [query_user]

    account = await get_certain_account_service(account_name="account_name", session=mock_session, user_id=2)

    assert type(account) == UserAccount
    assert account.account_name == "account_name"
    assert account.balance == 2500.0
    assert account.created_at == time

@pytest.mark.asyncio
async def test_get_all_accounts_service_more_then_zero_accounts():
    mock_session = AsyncMock()
    fake_accounts = [
        Account(name="first_test_name", user_id=1, balance=2500.0, created_at=datetime(2025, 8, 22, tzinfo=timezone.utc)),
        Account(name="second_test_name", user_id=1, balance=2500.0, created_at=datetime(2025, 8, 23, tzinfo=timezone.utc))
    ]
    fake_user = User(
        first_name="First_test",
        last_name="Last_test",
        username="test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=True,
        accounts=fake_accounts
    )

    query_user = MagicMock()
    query_user.scalar.return_value = fake_user

    mock_session.execute.return_value = query_user

    accounts = await get_all_accounts_service(username="test", session=mock_session)

    assert type(accounts[0]) == UserAccount
    assert type(accounts[1]) == UserAccount


@pytest.mark.asyncio
async def test_get_all_accounts_service_zero_accoutns():
    mock_session = AsyncMock()
    fake_user = User(
        first_name="First_test",
        last_name="Last_test",
        username="test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=True,
        accounts=[]
    )

    query_user = MagicMock()
    query_user.scalar.return_value = fake_user

    mock_session.execute.return_value = query_user

    accounts = await get_all_accounts_service(username="test", session=mock_session)

    assert len(accounts) == 0

@pytest.mark.asyncio
async def test_deposit_account_balance_service_greater_than_zero():
    mock_session = AsyncMock()
    fake_account = Account(name="account_name", user_id=1, balance=5000.0, created_at=datetime(2025, 8, 26, tzinfo=timezone.utc))

    with patch("app.services.banking.get_account", AsyncMock(return_value=fake_account)):
        with patch("app.services.banking.save_transaction") as mock_save:

            await deposit_account_balance_service(account_name="account_name", amount=1000.0, session=mock_session, user_id=1)

            assert fake_account.balance == 6000.0
            mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_deposit_account_balance_service_less_or_equal_zero():
    mock_session = AsyncMock()
    fake_account = Account(name="account_name", user_id=1, balance=5000.0, created_at=datetime(2025, 8, 26, tzinfo=timezone.utc))

    with patch("app.services.banking.get_account", AsyncMock(return_value=fake_account)):
            with pytest.raises(HTTPException) as exc:
                await deposit_account_balance_service(account_name="account_name", amount=-5000.0, session=mock_session, user_id=1)

            assert exc.value.status_code == 400
            assert exc.value.detail == "Amount must be greater than zero"

@pytest.mark.asyncio
async def test_transfer_money_service_amount_less_or_equal_than_zero():
    mock_session = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await transfer_money_service(
            account_name="account_name",
            amount=-1500.0,
            session=mock_session,
            user_id=1,
            transfer_account_name=None
        )
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_transfer_money_service_amount_less_than_balance():
    mock_session = AsyncMock()
    fake_account = Account(name="first_account", user_id=1, balance=5000.0, created_at=datetime(2025, 8, 24, tzinfo=timezone.utc))

    with patch("app.services.banking.get_account", AsyncMock(return_value=fake_account)), \
        pytest.raises(HTTPException) as exc:
        await transfer_money_service(
            account_name="account_name",
            amount=6000.0,
            session=mock_session,
            user_id=1,
            transfer_account_name=None
        )

        assert exc.value.status_code == 400
        assert exc.value.detail == "There are insufficient funds in the account"

@pytest.mark.asyncio
async def test_transfer_money_service_transfer_to_another_acc():
    mock_session = AsyncMock()
    from_fake_account = Account(name="first_account", user_id=1, balance=5000.0, created_at=datetime(2025, 8, 24, tzinfo=timezone.utc))
    to_fake_account = Account(name="second_account", user_id=1, balance=2000.0, created_at=datetime(2025, 8, 26, tzinfo=timezone.utc))

    with patch("app.services.banking.get_account", new_callable=AsyncMock) as mock_get_account:
        mock_get_account.side_effect = [from_fake_account, to_fake_account]
        with patch("app.services.banking.save_transaction") as mock_save:
            await transfer_money_service(
                account_name="first_account",
                amount=1000.0,
                session=mock_session,
                user_id=1,
                transfer_account_name="second_account"
            )

            assert from_fake_account.balance == 4000.0
            assert to_fake_account.balance == 3000.0
            mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_transfer_money_service_transfer_to_another_user():
    mock_session = AsyncMock()
    from_fake_account = Account(name="first_account", user_id=1, balance=13000.0, created_at=datetime(2025, 8, 24, tzinfo=timezone.utc))
    to_fake_account = Account(name="second_account", user_id=1, balance=7000.0, created_at=datetime(2025, 8, 26, tzinfo=timezone.utc))
    to_user = User(
        first_name="to_First_test",
        last_name="to_Last_test",
        username="to_test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=True,
        accounts=[to_fake_account]
    )

    with patch("app.services.banking.get_account", new_callable=AsyncMock) as mock_get_account, \
    patch("app.services.banking.get_user_from_db", new_callable=AsyncMock) as mock_user, \
    patch("app.services.banking.save_transaction") as mock_save:
        mock_get_account.side_effect = [from_fake_account, to_fake_account]
        mock_user.return_value = to_user

        await transfer_money_service(
            account_name="first_account",
            amount=5000.0,
            session=mock_session,
            user_id=1,
            transfer_account_name="second_account",
            transfer_username="to_test"
        )

        assert from_fake_account.balance == 8000.0
        assert to_fake_account.balance == 12000.0
        mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_get_transaction_history_service_from_cache():
    mock_session = AsyncMock()
    fake_user = User(
        first_name="Test",
        last_name="Test",
        username="test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=True
    )
    fake_transactions = [
        TransactionHistory(
            description="Пополнение счета",
            amount="+1000.0"
        ),
        TransactionHistory(
            description="Перевод со счета first_account на second_account",
            amount="+1000.0"
        )
    ]

    with patch("app.services.banking.get_user_from_db") as mock_user, \
    patch("app.services.banking.check_user_cache_transaction") as mock_check_cache, \
    patch("app.services.banking.get_transaction_history_redis") as mock_cache:
        mock_user.return_value = fake_user
        mock_check_cache.return_value = True
        mock_cache.return_value = fake_transactions

        result = await get_transaction_hisotry_service(
            user_data=UserOut(first_name="Test", last_name="Test", username="test"),
            account_name="first_account",
            session=mock_session
        )

        assert len(result) == 2
        assert type(result[0]) == TransactionHistory
        assert type(result[1]) == TransactionHistory
        assert result[0].description == "Пополнение счета"
        assert result[0].amount == "+1000.0"

@pytest.mark.asyncio
async def test_get_transaction_history_service_from_db():
    mock_session = AsyncMock()
    fake_account = Account(
        name="first_account",
        user_id=1,
        balance=55000.0,
        created_at=datetime(2025,8, 11, tzinfo=timezone.utc)
    )
    fake_transactions = [
        Transaction(
            user_id=1,
            from_account_id=None,
            to_account_id=1,
            amount=1000.0,
            timestamp=datetime(2025, 8, 12, tzinfo=timezone.utc),
            description="Пополнение счета"
        ),
        Transaction(
            user_id=1,
            from_account_id=1,
            to_account_id=4,
            amount=51000.0,
            timestamp=datetime(2025, 8, 15, tzinfo=timezone.utc),
            description="Перевод со счета first_account на fourth_account"
        )
    ]
    fake_user = User(
        first_name="Test",
        last_name="Test",
        username="test",
        hashed_password="hashed_password",
        email="test@gmail.com",
        is_email_verified=True,
    )

    with patch("app.services.banking.get_user_from_db") as mock_user, \
        patch("app.services.banking.check_user_cache_transaction") as mock_cache_check, \
        patch("app.services.banking.get_account") as mock_account, \
        patch("app.services.banking.save_transaction") as mock_save:

        mock_user.return_value = fake_user
        mock_cache_check.return_value = False
        mock_account.return_value = fake_account
        mock_history_query = MagicMock()
        mock_history_query.scalars.return_value.all.return_value = fake_transactions
        mock_session.execute.return_value = mock_history_query


        result = await get_transaction_hisotry_service(
            user_data=UserOut(first_name="Test", last_name="Test", username="test"),
            account_name="first_account",
            session=mock_session
        )

        assert len(result) == len(fake_transactions)
        assert mock_save.call_count == len(fake_transactions)
        assert type(result[0]) == TransactionHistory
        assert result[0].description == "Пополнение счета"
        assert result[1].description == "Перевод со счета first_account на fourth_account"

@pytest.mark.asyncio
async def test_delete_account_service():
    mock_session = AsyncMock()
    mock_user = MagicMock()
    mock_user.username = "test_user"
    fake_account = Account(
        name="first_account",
        user_id=1,
        balance=55000.0,
        created_at=datetime(2025,8, 11, tzinfo=timezone.utc)
    )
    fake_account.user = mock_user

    with patch("app.services.banking.get_account", new_callable=AsyncMock) as mock_get_account:
        mock_get_account.return_value = fake_account

        await delete_account_service(account_name="first_account", session=mock_session, user_id=1)

        mock_get_account.assert_awaited_once_with(acc_name="first_account", session=mock_session, user_id=1)
        mock_session.delete.assert_awaited_once_with(fake_account)
        mock_session.commit.assert_awaited_once()