"""Local-media probes for subtitle and lyric coverage.

Async variants use asyncio.create_subprocess_exec for ffprobe so many
files can be checked concurrently without blocking the event loop.
Callers pass a Semaphore to cap total concurrent ffprobe processes.
"""
import asyncio
import logging
import os
from typing import Optional

from core.cache import get_cache

logger = logging.getLogger(__name__)

_SUBTITLE_EXTS = {
    ".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx", ".sup", ".smi",
    ".mks", ".dfxp", ".ttml", ".sbv",
}

VIDEO_EXTS = {
    ".mkv", ".mp4", ".m4v", ".avi", ".mov", ".wmv", ".flv", ".ts", ".webm",
    ".m2ts", ".mts", ".iso", ".mpg", ".mpeg", ".rmvb", ".rm", ".vob",
    ".3gp", ".f4v",
}

AUDIO_EXTS = {
    ".mp3", ".flac", ".m4a", ".m4b", ".ogg", ".oga", ".opus",
    ".wav", ".ape", ".wma", ".aac", ".aiff", ".alac",
    ".dsf", ".dff",
    ".wv", ".tta", ".tak",
}

_CACHE_TTL = 60 * 60 * 24 * 365


def _signature(path: str) -> Optional[str]:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return f"{path}:{int(st.st_mtime)}:{st.st_size}"


def has_external_subtitle(video_path: str) -> bool:
    """True iff a sibling subtitle file shares the video's basename root."""
    folder = os.path.dirname(video_path)
    base = os.path.splitext(os.path.basename(video_path))[0]
    try:
        entries = os.listdir(folder)
    except OSError:
        return False
    for name in entries:
        ext = os.path.splitext(name)[1].lower()
        if ext not in _SUBTITLE_EXTS:
            continue
        sub_base = os.path.splitext(name)[0]
        if sub_base == base or sub_base.startswith(base + "."):
            return True
    return False


async def async_has_embedded_subtitle(
    video_path: str, sem: asyncio.Semaphore
) -> bool:
    """Run ffprobe asynchronously; acquire sem before spawning the process."""
    sig = _signature(video_path)
    if sig is None:
        return False
    key = f"subprobe:embedded:{sig}"
    cache = get_cache()
    cached = cache.get(key)
    if cached is not None:
        return cached == "1"

    async with sem:
        try:
            proc = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v", "error",
                "-select_streams", "s",
                "-show_entries", "stream=index",
                "-of", "csv=p=0",
                video_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                logger.warning("ffprobe timed out on %s", video_path)
                return False
        except FileNotFoundError:
            logger.warning("ffprobe not installed; embedded-subtitle check disabled")
            return False
        except OSError as exc:
            logger.warning("ffprobe failed on %s: %s", video_path, exc)
            return False

    has_sub = bool(stdout.strip())
    cache.setex(key, _CACHE_TTL, "1" if has_sub else "0")
    return has_sub


async def async_has_subtitle(video_path: str, sem: asyncio.Semaphore) -> bool:
    """External check is sync+fast (listdir); embedded check is async ffprobe."""
    if has_external_subtitle(video_path):
        return True
    return await async_has_embedded_subtitle(video_path, sem)


def has_lyrics(audio_path: str) -> bool:
    """True iff the audio file carries embedded lyrics in its tag block."""
    sig = _signature(audio_path)
    if sig is None:
        return False
    key = f"lyrprobe:{sig}"
    cache = get_cache()
    cached = cache.get(key)
    if cached is not None:
        return cached == "1"

    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return False

    try:
        meta = MutagenFile(audio_path)
    except Exception as exc:
        logger.warning("mutagen failed on %s: %s", audio_path, exc)
        cache.setex(key, _CACHE_TTL, "0")
        return False

    try:
        has_lyr = _tags_carry_lyrics(meta)
    except Exception as exc:
        logger.warning("lyric tag inspection failed for %s: %s", audio_path, exc)
        has_lyr = False
    cache.setex(key, _CACHE_TTL, "1" if has_lyr else "0")
    return has_lyr


def _tags_carry_lyrics(meta) -> bool:
    if meta is None:
        return False
    tags = getattr(meta, "tags", None)
    if tags is None:
        return False

    getall = getattr(tags, "getall", None)
    if callable(getall):
        if getall("USLT") or getall("SYLT"):
            return True

    for key in (
        "lyrics", "LYRICS", "Lyrics", "UNSYNCEDLYRICS",
        "\xa9lyr",
        "----:com.apple.iTunes:LYRICS",
        "WM/Lyrics",
    ):
        try:
            value = tags.get(key)
        except (AttributeError, TypeError, ValueError, KeyError):
            continue
        if value:
            return True
    return False
