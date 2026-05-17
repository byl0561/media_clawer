"""Parallel local-library scanning.

Replaces ``utils.file_utils``. Same map/filter semantics, but:

* a missing library root yields ``[]`` instead of raising (the folder may be
  an unmounted volume in production);
* the worker count is configurable instead of a hard-coded ``12``;
* the process pool is always cleaned up via a context manager.
"""
import multiprocessing
import os
from functools import partial
from typing import Any, Callable, List

from core import conf

__all__ = ["scan_files", "scan_dirs"]


def _collect_files(path: str, name_filter: Callable[[str], bool]) -> List[str]:
    matched = []
    for root, _dirs, files in os.walk(path):
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
        if os.path.isdir(os.path.join(root, name))
    ]


def _run(root, collector, name_filter, mapper) -> List[Any]:
    subdirs = _top_level_subdirs(root)
    if not subdirs:
        return []
    with multiprocessing.Pool(conf.SCAN_WORKERS) as pool:
        nested = pool.map(partial(collector, name_filter=name_filter), subdirs)
        paths = [p for sub in nested for p in sub]
        objects = pool.map(mapper, paths)
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
