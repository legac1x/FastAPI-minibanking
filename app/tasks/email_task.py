import re
import smtplib
from email.mime.text import MIMEText
from fastapi import HTTPException, status

from app.core.celery import celery_app
from app.core.config import settings
from app.core.logging import logger

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to_email: str, verification_code: int):
    logger.info("Формирование сообщения с кодом верификации для %s", to_email)

    email_text = f"""Для подтвреждения авторизации введите код: {verification_code}

Если вы не запрашивали этот код, проигнорируйте это письмо."""
    msg = MIMEText(email_text)
    msg["Subject"] = "Код подтверждения для авторизации"
    msg["From"] = settings.EMAIL_HOST
    msg["To"] = to_email

    try:
        logger.debug("Подключение к SMTP серверу Яндекс: %s:%s", "smtp.yandex.ru", 587)
        with smtplib.SMTP("smtp.yandex.ru", 587) as server:
            server.starttls()
            logger.debug("Аутентификация на SMTP сервере")
            server.login(settings.EMAIL_HOST, settings.EMAIL_PASSWORD)
            logger.debug("Отправка письма с кодом верификации на %s", to_email)
            server.sendmail(settings.EMAIL_HOST, to_email, msg.as_string())
        logger.info("Успешная отправка сообщения с кодом верификации на почту '%s'", to_email)
        return "Message successfully sent!"
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("Ошибка аутентификации на SMTP сервере при отправке письма на %s. Повторная попытка", to_email)
        raise self.retry(exc=exc)
    except smtplib.SMTPException as exc:
        logger.warning("Ошибка SMTP при отправке сообщения на %s: %s. Повторная попытка", to_email, exc)
        raise self.retry(exc=exc)
    except Exception as exc:
        logger.warning("Неожиданная ошибка при отправке сообщения на %s: %s. Повторная попытка", to_email, exc)
        raise self.retry(exc=exc)
