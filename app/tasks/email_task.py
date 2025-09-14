import re
import smtplib
from email.mime.text import MIMEText

from app.core.celery import celery_app
from app.core.config import settings


@celery_app.task
def send_email(to_email: str, verification_code: int):
    msg = MIMEText(f"Для авторизации подтвердите введите код {verification_code}")
    msg["Subject"] = "Подтверждение пароля"
    msg["From"] = settings.EMAIL_HOST
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.yandex.ru", 587) as server:
            server.starttls()
            server.login(settings.EMAIL_HOST, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_HOST, to_email, msg.as_string())
        return "Message successfully sent!"
    except Exception as exc:
        print(exc)
