"""Celery task that runs a backtest asynchronously, plus the dispatch helper used
by the API layer. If the Celery broker is unreachable (e.g. local dev without
Redis running), `dispatch_backtest` falls back to executing synchronously in the
request process — the API stays usable without extra setup, while `docker compose
up` (with Redis + a worker) always takes the real async path.

Kombu's own connect-retry-with-backoff (used internally by `send_task`) does not
reliably honor the short `broker_connection_*` timeouts when the broker refuses
the connection outright, and can block for well over a minute. Rather than fight
that, `dispatch_backtest` does its own fast raw-socket reachability check first,
so the synchronous fallback kicks in within ~1.5s instead.
"""

import socket
from urllib.parse import urlparse

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _broker_reachable(url: str, timeout: float = 1.5) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@celery_app.task(name="run_backtest")
def run_backtest_task(backtest_id: int) -> None:
    from app.db.session import SessionLocal
    from app.services.backtest_service import BacktestService

    db = SessionLocal()
    try:
        BacktestService(db).execute(backtest_id)
    finally:
        db.close()


def dispatch_backtest(backtest_id: int) -> None:
    if _broker_reachable(settings.CELERY_BROKER_URL):
        try:
            celery_app.send_task("run_backtest", args=[backtest_id])
            logger.info("backtest_enqueued", backtest_id=backtest_id)
            return
        except Exception as exc:  # noqa: BLE001 — still fall back rather than fail the request
            logger.warning("celery_send_failed_running_synchronously", backtest_id=backtest_id, error=str(exc))
    else:
        logger.warning("celery_broker_unreachable_running_backtest_synchronously", backtest_id=backtest_id)

    run_backtest_task(backtest_id)
