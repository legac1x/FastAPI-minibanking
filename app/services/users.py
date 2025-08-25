from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.users import SignUp
from app.db.models import User, Account
from app.core.security import get_hashed_password
from app.services.email import send_email_verification_code

async def sign_up_user_services(user_data: SignUp, session: AsyncSession):
    hashed_password = get_hashed_password(user_data.password)
    user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email
    )
    new_account = Account(user=user)
    session.add_all([user, new_account])
    await session.commit()

    await send_email_verification_code(user=user, session=session)