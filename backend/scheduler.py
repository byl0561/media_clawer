"""APScheduler cron jobs — replaces django-crontab.

Original schedule (cron syntax → APScheduler):
  30 4 * * 1  book    (Monday    04:30)
  30 4 * * 2  movie   (Tuesday   04:30)
  30 4 * * 3  music   (Wednesday 04:30)
  30 4 * * 4  tvshow  (Thursday  04:30)
"""
import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from book import cron as book_cron
from movie import cron as movie_cron
from music import cron as music_cron
from tvshow import cron as tvshow_cron

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    _scheduler.add_job(book_cron.cronjob,   "cron", day_of_week="mon", hour=4, minute=30)
    _scheduler.add_job(movie_cron.cronjob,  "cron", day_of_week="tue", hour=4, minute=30)
    _scheduler.add_job(music_cron.cronjob,  "cron", day_of_week="wed", hour=4, minute=30)
    _scheduler.add_job(tvshow_cron.cronjob, "cron", day_of_week="thu", hour=4, minute=30)
    _scheduler.start()
    logger.info("scheduler started")
    return _scheduler
