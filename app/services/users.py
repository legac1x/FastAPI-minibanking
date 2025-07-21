from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.users import SignUp
from app.db.models import User, Account
from app.core.security import get_hashed_password

async def sign_up_user_services(user_data: SignUp, session: AsyncSession):
    hashed_password = get_hashed_password(user_data.password)
    user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    new_account = Account(user=user)
    session.add_all([user, new_account])
    await session.commit()