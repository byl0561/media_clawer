"""Weekly cache pre-warm for the book diff (see settings.CRONJOBS)."""
from core.cron import run_job
from book import services


def cronjob() -> None:
    run_job("book", services.refresh_all)
