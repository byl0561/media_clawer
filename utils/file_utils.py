import multiprocessing
import os

from typing import Any, Callable
from functools import partial

__all__ = ['mapping_file_to_object']


def collect_files_in_directory(file_name: str, file_name_filter: Callable[[str], bool]) -> list[str]:
    file_list = []
    for root, dirs, files in os.walk(file_name):
        for file in files:
            if file_name_filter(file):
                file_list.append(os.path.join(root, file))
    return file_list


def mapping_file_to_object(root: str, file_name_filter: Callable[[str], bool], mapper: Callable[[str], Any]) -> \
        list[Any]:
    with multiprocessing.Pool(8) as pool:
        subdirectories = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        results = pool.map(partial(collect_files_in_directory, file_name_filter=file_name_filter), subdirectories)
        files = [file for sublist in results for file in sublist]

        obj_lists = pool.map(mapper, files)

        return [obj for obj in obj_lists]
