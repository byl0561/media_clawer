import multiprocessing
import os

from typing import Any, Callable
from functools import partial

__all__ = ['mapping_file_to_object', 'mapping_dir_to_object']


worker_num = 12


def collect_files_in_directory(path: str,
                               file_name_filter: Callable[[str], bool]) -> list[str]:
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file_name_filter(file):
                file_list.append(os.path.join(root, file))
    return file_list


def mapping_file_to_object(root: str,
                           file_name_filter: Callable[[str], bool],
                           mapper: Callable[[str], Any]) -> list[Any]:
    with multiprocessing.Pool(worker_num) as pool:
        subdirectories = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        results = pool.map(partial(collect_files_in_directory, file_name_filter=file_name_filter), subdirectories)
        files = [file for sublist in results for file in sublist]

        obj_lists = pool.map(mapper, files)

        objs = [obj for obj in obj_lists]
        return list(filter(lambda x: x is not None, objs))


def collect_dirs_in_directory(path: str,
                              dir_name_filter: Callable[[str], bool]) -> list[str]:
    dir_list = []

    _, d = os.path.split(path)
    if dir_name_filter(d):
        dir_list.append(path)

    for root, dirs, files in os.walk(path):
        for d in dirs:
            if dir_name_filter(d):
                dir_list.append(os.path.join(root, d))
    return dir_list


def mapping_dir_to_object(root: str,
                          dir_name_filter: Callable[[str], bool],
                          mapper: Callable[[str], Any]) -> list[Any]:
    with multiprocessing.Pool(worker_num) as pool:
        subdirectories = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        results = pool.map(partial(collect_dirs_in_directory, dir_name_filter=dir_name_filter), subdirectories)
        dirs = [d for sublist in results for d in sublist]

        obj_lists = pool.map(mapper, dirs)

        objs = [obj for obj in obj_lists]
        return list(filter(lambda x: x is not None, objs))
