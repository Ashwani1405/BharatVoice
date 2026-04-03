from celery import Celery
from app.config import settings

celery_app = Celery(
    "bharatvoice_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)

# Important: these autodiscover modules need to be defined
celery_app.autodiscover_tasks(["app.tasks.kyc_tasks", "app.tasks.fraud_tasks", "app.tasks.notification_tasks"])
