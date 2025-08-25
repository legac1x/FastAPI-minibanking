import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.tasks.email_task import send_email
from app.db.models import User

def generate_verification_code() -> int:
    return random.randint(100000, 999999)

async def send_email_verification_code(user: User, session: AsyncSession):
    verification_code = generate_verification_code()
    verification_code_expire = datetime.now() + timedelta(minutes=15)

    user.email_verification_code = verification_code
    user.email_verification_code_expires = verification_code_expire

    await session.commit()

    send_email.delay(user.email, verification_code)

async def verify_user_code(user_code: int, email: str, session: AsyncSession):
    user_query = await session.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()

    if user is None:
        return False

    current_time = datetime.now()

    if user_code == int(user.email_verification_code) and current_time < user.email_verification_code_expires:
        user.is_email_verified = True
        user.email_verification_code = None
        user.email_verification_code_expires = None
        await session.commit()
        return True

    return False
