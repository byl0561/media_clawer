"""Weekly cache pre-warm for the TV/anime diffs (see settings.CRONJOBS)."""
from core.cron import run_job
from tvshow import services


def cronjob() -> None:
    run_job("tvshow", services.refresh_all, services.warm_subtitle_cache)
