from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "notification_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_queues={
        "critical": {"exchange": "critical", "routing_key": "critical"},
        "high": {"exchange": "high", "routing_key": "high"},
        "normal": {"exchange": "normal", "routing_key": "normal"},
        "low": {"exchange": "low", "routing_key": "low"},
    },
    task_default_queue="normal",
    worker_concurrency=4,
    broker_transport_options={
        "priority_steps": list(range(10)),
        "sep": ":",
        "queue_order_strategy": "priority",
    },
)
