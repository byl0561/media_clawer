import os
import re

from book.models.book import LocalBook
from utils import file_utils


def file_filter(file: str) -> bool:
    pattern = r'^(.+)\s-\s(.+)\.(\w+)'
    return re.match(pattern, file) is not None


def process_file(path: str):
    _, file = os.path.split(path)

    pattern = r'^(.+)\s-\s(.+)\.(\w+)'
    match = re.match(pattern, file)
    if not match:
        return None

    title = match.group(1)
    author = match.group(2)
    author = re.sub(r'\[[^]]*]', '', author).strip()
    author = re.sub(r'\([^]]*\)', '', author)
    author = re.sub(r'（[^]]*）', '', author)
    return LocalBook(title, author)


def crawl_local(book_folder: str) -> list[LocalBook]:
    return file_utils.mapping_file_to_object(book_folder, file_filter, process_file)
