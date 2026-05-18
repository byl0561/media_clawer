"""Weekly cache pre-warm for the movie diffs (see settings.CRONJOBS)."""
from core.cron import run_job
from movie import services


def cronjob() -> None:
    run_job("movie", services.refresh_all)
