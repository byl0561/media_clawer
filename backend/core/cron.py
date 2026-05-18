"""Uniform cron-job wrapper.

The four ``utils/cron.py`` modules each repeated the same try/except/log
boilerplate and swallowed tracebacks (``logger.error(e)``). ``run_job`` runs
the steps in order, logs full tracebacks on failure and never lets one job
take the scheduler down.
"""
import logging
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = ["run_job"]


def run_job(name: str, *steps: Callable[[], object]) -> None:
    logger.warning("%s cronjob start", name)
    try:
        for step in steps:
            step()
    except Exception:
        logger.exception("%s cronjob failed", name)
    else:
        logger.warning("%s cronjob succeed", name)
