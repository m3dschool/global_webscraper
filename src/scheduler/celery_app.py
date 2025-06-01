from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "webscraper",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.scheduler.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'check-scheduled-jobs': {
        'task': 'src.scheduler.tasks.check_scheduled_jobs',
        'schedule': 60.0,  # Check every minute
    },
}

if __name__ == '__main__':
    celery_app.start()