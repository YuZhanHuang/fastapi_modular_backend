from celery_sqlalchemy_scheduler.schedulers import DatabaseScheduler


class AppDatabaseScheduler(DatabaseScheduler):
    """Database-backed beat scheduler without Celery's built-in default entries."""

    def setup_schedule(self) -> None:
        self.update_from_dict(self.app.conf.beat_schedule)
