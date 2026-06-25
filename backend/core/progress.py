"""ProgressSink — passes progress events from service functions to the SSE generator."""
import asyncio
from typing import Optional


class ProgressSink:
    """Put progress dicts onto a queue; routers/__init__.py drains and flushes them."""

    __slots__ = ("_q",)

    def __init__(self, q: "asyncio.Queue[Optional[dict]]") -> None:
        self._q = q

    async def report(self, step: str, pct: int) -> None:
        await self._q.put({"step": step, "pct": pct})
