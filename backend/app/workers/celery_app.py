"""Celery application configuration."""
from celery import Celery
from app.core.config import settings


celery_app = Celery(
    "lexchain",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "app.workers.tasks.send_email": {"queue": "emails"},
        "app.workers.tasks.process_document": {"queue": "documents"},
        "app.workers.tasks.run_compliance_check": {"queue": "compliance"},
        "app.workers.tasks.process_ai_analysis": {"queue": "ai"},
        "app.workers.tasks.anchor_to_blockchain": {"queue": "blockchain"},
        "app.workers.tasks.generate_report": {"queue": "reports"},
    },
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.workers.tasks.cleanup_expired_sessions",
            "schedule": 3600.0,
        },
        "check-compliance-expiry": {
            "task": "app.workers.tasks.check_compliance_expiry",
            "schedule": 86400.0,
        },
    }
)