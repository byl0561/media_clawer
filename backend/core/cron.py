"""Uniform cron-job wrapper.

All steps (sync and async) run inside a single asyncio.run() so they share
one event loop and one httpx client for the duration of the job. The client
is closed after all steps complete.
"""
import asyncio
import inspect
import logging
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = ["run_job"]


async def _run_steps(*steps: Callable[[], object]) -> None:
    try:
        for step in steps:
            if inspect.iscoroutinefunction(step):
                await step()
            else:
                step()
    finally:
        from core.http import close_async_client
        await close_async_client()


def run_job(name: str, *steps: Callable[[], object]) -> None:
    logger.warning("%s cronjob start", name)
    try:
        asyncio.run(_run_steps(*steps))
    except Exception:
        logger.exception("%s cronjob failed", name)
    else:
        logger.warning("%s cronjob succeed", name)
