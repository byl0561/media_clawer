"""SSE streaming helper shared by all domain routers."""
import asyncio
import json
from typing import AsyncIterator, Callable

from fastapi.responses import StreamingResponse

from core.exceptions import UpstreamUnavailable
from core.progress import ProgressSink

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_result(fn: Callable, progress_msg: str = "正在处理…") -> StreamingResponse:
    """Stream a service call as SSE with live progress.

    ``fn`` receives a ProgressSink as its first argument and must call
    ``await sink.report(step, pct)`` to push progress events.  The SSE
    generator drains the queue in real time; a heartbeat comment fires every
    10 s so nginx/CDN proxies don't time out between events.
    """

    async def generate() -> AsyncIterator[str]:
        q: asyncio.Queue = asyncio.Queue()
        sink = ProgressSink(q)

        yield _sse("progress", {"step": progress_msg, "pct": 0})

        if asyncio.iscoroutinefunction(fn):
            coro = fn(sink)
        else:
            maybe = fn(sink)
            if asyncio.iscoroutine(maybe):
                coro = maybe
            else:
                yield _sse("result", maybe)
                return

        task = asyncio.create_task(coro)
        # Wake the queue reader immediately when the task finishes.
        task.add_done_callback(lambda _: q.put_nowait(None))

        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=10.0)
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"
                continue
            if msg is None:  # sentinel — task is done
                break
            yield _sse("progress", msg)

        try:
            yield _sse("result", task.result())
        except UpstreamUnavailable:
            yield _sse("error", {"code": "upstream_unavailable", "detail": "上游榜单数据暂不可用"})
        except Exception as exc:
            yield _sse("error", {"code": "error", "detail": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)
