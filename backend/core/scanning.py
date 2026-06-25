"""Parallel local-library scanning using a thread pool.

Thread pool replaces multiprocessing.Pool because the bottleneck is NFS I/O
(not CPU): the GIL is released during I/O syscalls so threads parallelize
reads as effectively as processes, without the process-spawn overhead
(~0.5 s per worker on macOS where multiprocessing uses 'spawn').
"""
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, List

from core import conf

__all__ = ["scan_files", "scan_dirs"]

_EXCLUDED_DIRS = {
    "#recycle",        # Synology
    "@Recycle",        # QNAP
    "$RECYCLE.BIN",    # Windows Vista+
    "RECYCLER",        # Windows XP
    ".Trash",          # Linux / generic
    ".Trashes",        # macOS (volume-level)
    ".Trash-1000",     # Linux freedesktop (uid 1000)
}


def _excluded(name: str) -> bool:
    return name in _EXCLUDED_DIRS or name.startswith(".Trash-")


def _prune(dirs: List[str]) -> None:
    dirs[:] = [d for d in dirs if not _excluded(d)]


def _collect_files(path: str, name_filter: Callable[[str], bool]) -> List[str]:
    matched = []
    for root, dirs, files in os.walk(path):
        _prune(dirs)
        for file in files:
            if name_filter(file):
                matched.append(os.path.join(root, file))
    return matched


def _collect_dirs(path: str, name_filter: Callable[[str], bool]) -> List[str]:
    matched = []
    _, leaf = os.path.split(path)
    if name_filter(leaf):
        matched.append(path)
    for root, dirs, _files in os.walk(path):
        _prune(dirs)
        for d in dirs:
            if name_filter(d):
                matched.append(os.path.join(root, d))
    return matched


def _top_level_subdirs(root: str) -> List[str]:
    if not os.path.isdir(root):
        return []
    return [
        os.path.join(root, name)
        for name in os.listdir(root)
        if not _excluded(name) and os.path.isdir(os.path.join(root, name))
    ]


def _run(root, collector, name_filter, mapper) -> List[Any]:
    subdirs = _top_level_subdirs(root)
    if not subdirs:
        return []
    collect = partial(collector, name_filter=name_filter)
    with ThreadPoolExecutor(max_workers=conf.SCAN_WORKERS) as pool:
        nested = list(pool.map(collect, subdirs))
        paths = [p for sub in nested for p in sub]
        objects = list(pool.map(mapper, paths))
    return [obj for obj in objects if obj is not None]


def scan_files(
    root: str,
    name_filter: Callable[[str], bool],
    mapper: Callable[[str], Any],
) -> List[Any]:
    """Map every file under ``root`` matching ``name_filter`` through ``mapper``."""
    return _run(root, _collect_files, name_filter, mapper)


def scan_dirs(
    root: str,
    name_filter: Callable[[str], bool],
    mapper: Callable[[str], Any],
) -> List[Any]:
    """Map every directory under ``root`` matching ``name_filter`` through ``mapper``."""
    return _run(root, _collect_dirs, name_filter, mapper)
