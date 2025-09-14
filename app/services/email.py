import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.tasks.email_task import send_email
from app.db.models import User
from app.core.logging import logger

def generate_verification_code() -> int:
    logger.debug("Формирование случайного кода верификации")
    return random.randint(100000, 999999)

async def send_email_verification_code(user: User, session: AsyncSession):
    logger.info("Отправка письма с кодом верификации на почту '%s'", user.email)
    verification_code = generate_verification_code()
    logger.debug("Присвоение пользователю код и время истечения кода")
    verification_code_expire = datetime.now() + timedelta(minutes=15)

    user.email_verification_code = verification_code
    user.email_verification_code_expires = verification_code_expire

    await session.commit()
    logger.debug("Формирование задачи Celery для отправки письма")
    send_email.delay(user.email, verification_code)

async def verify_user_code(user_code: int, email: str, session: AsyncSession):
    logger.info("Верификация пользователя '%s'", email)
    user_query = await session.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()

    if user is None:
        logger.warning("Пользователь с почтой '%s' не найден", email)
        return False

    current_time = datetime.now()
    logger.debug("Проверка совпадения кода верификации и его истечения")
    if user_code == int(user.email_verification_code) and current_time < user.email_verification_code_expires:
        logger.debug("Код верификации совпадает и не истек")
        user.is_email_verified = True
        user.email_verification_code = None
        user.email_verification_code_expires = None
        logger.info("Успешная регистрация пользователя '%s'", user.username)
        await session.commit()
        return True
    logger.warning("Код истек или не совпадает")
    return False
