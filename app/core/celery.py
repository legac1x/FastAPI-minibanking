from celery import Celery

celery_app = Celery(
    "celery_app",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
    include=["app.tasks.email_task"]
)