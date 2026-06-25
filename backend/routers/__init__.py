"""SSE streaming helper shared by all domain routers."""
import asyncio
import json
from typing import AsyncIterator, Callable

from fastapi.responses import StreamingResponse

from core.exceptions import UpstreamUnavailable

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_result(fn: Callable, progress_msg: str = "正在处理…") -> StreamingResponse:
    """Stream a service call as SSE.

    Accepts both coroutine functions and plain callables that return a
    coroutine (e.g. ``lambda: services.series_gaps("tv")``).
    Sends a heartbeat comment every 10 s so nginx/CDN proxies don't time out.
    """

    async def generate() -> AsyncIterator[str]:
        yield _sse("progress", {"step": progress_msg, "pct": 0})

        # Resolve to a coroutine regardless of how fn is wrapped
        if asyncio.iscoroutinefunction(fn):
            coro = fn()
        else:
            maybe = fn()
            if asyncio.iscoroutine(maybe):
                coro = maybe
            else:
                # Already a plain value (sync fallback — shouldn't happen post-migration)
                yield _sse("result", maybe)
                return

        task = asyncio.create_task(coro)

        while not task.done():
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=10.0)
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"
            except Exception:
                break

        try:
            yield _sse("result", task.result())
        except UpstreamUnavailable:
            yield _sse("error", {"code": "upstream_unavailable", "detail": "上游榜单数据暂不可用"})
        except Exception as exc:
            yield _sse("error", {"code": "error", "detail": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)
