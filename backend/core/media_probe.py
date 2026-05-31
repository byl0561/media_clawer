"""Local-media probes for subtitle and lyric coverage.

Subtitle detection is split into two layers:

- :func:`has_external_subtitle` — sibling files in the same folder whose
  basename matches the video (allowing ``.zh`` / ``.eng`` / etc. suffixes).
- :func:`has_embedded_subtitle` — invokes ``ffprobe`` to enumerate subtitle
  streams inside the container. The Docker image installs ffmpeg; if
  ``ffprobe`` is missing for any reason (dev machine, container reshuffle)
  the function returns ``False`` so the worst case is a false positive on
  the "missing subtitle" list rather than a crash.

Lyric detection uses :mod:`mutagen` and checks the formats we actually
encounter in the album library: ID3 (mp3/wav), Vorbis comments (flac/ogg),
MP4 atoms (m4a), APE tags.

Both probes are cached by ``(path, mtime, size)`` in Django's cache (Redis)
so a full-library subtitle/lyric scan only pays the per-file probe cost on
the first run after a file change.
"""
import logging
import os
import subprocess
from typing import Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Subtitle file extensions placed next to the video. Covers SubRip,
# (Advanced) SubStation Alpha, WebVTT, VobSub, MicroDVD, PGS, MKV subs,
# TTML/DFXP, YouTube SBV. ``.txt`` is intentionally omitted — too many
# unrelated text files share that extension and would false-positive.
_SUBTITLE_EXTS = {
    ".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx", ".sup", ".smi",
    ".mks", ".dfxp", ".ttml", ".sbv",
}

# Container formats. ``.iso`` is allowed because ffprobe can enumerate
# subtitle streams inside DVD/BluRay images; ``.rmvb`` / ``.rm`` cover older
# Chinese-language libraries; ``.m2ts`` / ``.mts`` cover BluRay/AVCHD.
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

# 1 year — file mtime/size in the key invalidate naturally on edit.
_CACHE_TTL = 60 * 60 * 24 * 365


def _signature(path: str) -> Optional[str]:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return f"{path}:{int(st.st_mtime)}:{st.st_size}"


def has_external_subtitle(video_path: str) -> bool:
    """True iff a sibling subtitle file shares the video's basename root.

    Accepts language-suffixed variants (``movie.zh.srt``, ``movie.eng.ass``)
    by matching ``<base>`` or ``<base>.<lang>`` exactly.
    """
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


def has_embedded_subtitle(video_path: str) -> bool:
    """Run ffprobe to detect any subtitle stream inside the container.

    Returns ``False`` when ffprobe is unavailable or the probe times out —
    treating "we couldn't check" as "no embedded subtitle" makes the
    missing-subtitle list err on the safe side.
    """
    sig = _signature(video_path)
    if sig is None:
        return False
    key = f"subprobe:embedded:{sig}"
    cached = cache.get(key)
    if cached is not None:
        return cached == "1"

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "s",
                "-show_entries", "stream=index",
                "-of", "csv=p=0",
                video_path,
            ],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        logger.warning("ffprobe not installed; embedded-subtitle check disabled")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timed out on %s", video_path)
        return False
    except OSError as exc:
        logger.warning("ffprobe failed on %s: %s", video_path, exc)
        return False

    has_sub = bool(result.stdout.strip())
    cache.set(key, "1" if has_sub else "0", timeout=_CACHE_TTL)
    return has_sub


def has_subtitle(video_path: str) -> bool:
    """Either external sibling or embedded stream — same outcome to the user."""
    if has_external_subtitle(video_path):
        return True
    return has_embedded_subtitle(video_path)


def has_lyrics(audio_path: str) -> bool:
    """True iff the audio file carries embedded lyrics in its tag block."""
    sig = _signature(audio_path)
    if sig is None:
        return False
    key = f"lyrprobe:{sig}"
    cached = cache.get(key)
    if cached is not None:
        return cached == "1"

    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return False

    try:
        meta = MutagenFile(audio_path)
    except Exception as exc:  # mutagen raises a grab-bag of format errors
        logger.warning("mutagen failed on %s: %s", audio_path, exc)
        cache.set(key, "0", timeout=_CACHE_TTL)
        return False

    try:
        has_lyr = _tags_carry_lyrics(meta)
    except Exception as exc:
        # Defensive: tag-format quirks shouldn't escape from a probe call.
        logger.warning("lyric tag inspection failed for %s: %s", audio_path, exc)
        has_lyr = False
    cache.set(key, "1" if has_lyr else "0", timeout=_CACHE_TTL)
    return has_lyr


def _tags_carry_lyrics(meta) -> bool:
    if meta is None:
        return False
    tags = getattr(meta, "tags", None)
    if tags is None:
        return False

    # ID3 (mp3, wav): USLT (unsync) / SYLT (sync) frames are keyed by frame id
    # which may have a language suffix, so use getall().
    getall = getattr(tags, "getall", None)
    if callable(getall):
        if getall("USLT") or getall("SYLT"):
            return True

    # Vorbis comments (flac, ogg, opus), MP4 (m4a), ASF (wma), APE all expose
    # a dict-ish API; case variants come from different writers. Vorbis
    # comments reject any key with non-ASCII bytes by raising ValueError
    # (e.g. when we feed the MP4 ``\xa9lyr`` atom into a flac's tag store),
    # so the except has to cover that too.
    for key in (
        "lyrics", "LYRICS", "Lyrics", "UNSYNCEDLYRICS",
        "\xa9lyr",                            # MP4 / iTunes lyrics atom
        "----:com.apple.iTunes:LYRICS",        # MP4 freeform fallback
        "WM/Lyrics",                           # ASF / WMA
    ):
        try:
            value = tags.get(key)
        except (AttributeError, TypeError, ValueError, KeyError):
            continue
        if value:
            return True
    return False
