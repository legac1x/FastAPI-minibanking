from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "celery_app",
    broker=settings.REDIS_BROKER_URL,
    backend=settings.REDIS_BACKEND_URL,
    include=["app.tasks.email_task"]
)