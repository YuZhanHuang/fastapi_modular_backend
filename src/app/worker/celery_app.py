import pytz
from celery import Celery

from app.config import settings

celery = Celery("cart_service")

celery.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    beat_dburi=settings.DATABASE_URL,
    beat_schedule={},
    timezone=pytz.UTC,
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    imports=("app.worker.tasks",),
)
