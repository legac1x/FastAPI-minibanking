import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.api.schemas.users import SignUp
from app.db.models import User, Account
from app.core.security import get_hashed_password
from app.services.email import send_email_verification_code
from app.core.logging import logger

def _is_valid_email(email: str):
    if not email:
        return False, "Email не может быть пустым"
    if len(email) > 254:
        return False, f"Email слишком длинный ({len(email)} > 254 символов)"

    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*[a-zA-Z0-9]@[a-zA-Z0-9а-яА-ЯёЁ.-]+\.[a-zA-Zа-яА-ЯёЁ]{2,}$'
    if not re.match(pattern, email, re.IGNORECASE):
        if '@' not in email:
            return False, "Отсутствует символ @"

        parts = email.split('@')
        if len(parts) != 2:
            return False, "Некорректный формат email"

        local_part, domain = parts
        if not local_part:
            return False, "Пустая локальная часть (до @)"
        if not domain:
            return False, "Пустой домен (после @)"
        if '.' not in domain:
            return False, "Отсутствует точка в домене"

        domain_parts = domain.split('.')
        if len(domain_parts) < 2:
            return False, "Некорректный домен"

        tld = domain_parts[-1]
        if len(tld) < 2:
            return False, "Слишком короткий домен верхнего уровня"
        return False, "Некорректный формат email"
    return True, "OK"

async def sign_up_user_services(user_data: SignUp, session: AsyncSession):
    logger.info("Начало регистрации пользователя '%s'", user_data.username)
    hashed_password = get_hashed_password(user_data.password)
    user_query = await session.execute(select(User).where(or_(
        User.username == user_data.username,
        User.email == user_data.email
    )))
    users = user_query.scalars().all()
    if users:
        logger.warning("Пользователь с введенным никнеймом '%s' или почтой '%s' уже существует", user_data.username, user_data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this username or email already registered!"
        )

    is_valid, reason = _is_valid_email(user_data.email)
    if not is_valid:
        logger.warning(
            "Попытка регистрации с некорректным email '%s'. Пользователь - '%s', причина - '%s'",
            user_data.email,
            user_data.username,
            reason
        )
        return False

    user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email
    )
    logger.info("Сохранение нового пользователя '%s' в БД", user_data.username)
    new_account = Account(user=user)
    session.add_all([user, new_account])
    await session.commit()
    logger.debug("Отправка подтверждения регистрации по электронной почте '%s'", user_data.email)
    await send_email_verification_code(user=user, session=session)