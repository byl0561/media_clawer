"""Weekly cache pre-warm for the album diff (see settings.CRONJOBS)."""
from core.cron import run_job
from music import services


def cronjob() -> None:
    run_job("music", services.refresh_all)
