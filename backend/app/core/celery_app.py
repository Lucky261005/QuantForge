"""Celery application instance — used to run backtests asynchronously."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "quantforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.backtest_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600 * 24,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Fail fast if the broker is unreachable (e.g. local dev without Redis running)
    # instead of Kombu's default multi-minute retry-with-backoff — dispatch_backtest's
    # synchronous fallback should kick in within ~2s, not ~2 minutes.
    broker_connection_timeout=2,
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=1,
    broker_transport_options={"socket_connect_timeout": 2, "max_retries": 1},
)
