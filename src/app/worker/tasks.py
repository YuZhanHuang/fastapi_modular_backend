from app.worker.celery_app import celery


@celery.task(name="app.worker.tasks.ping")
def ping() -> str:
    """Simple health-check task for worker smoke tests."""
    return "pong"
