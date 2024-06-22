import os
import re

from book.models.book import LocalBook
from utils import file_utils


def file_filter(file: str) -> bool:
    pattern = r'^(.+)\s-\s(.+)\.(\w+)'
    return re.match(pattern, file) is not None


def process_file(path: str):
    root, file = os.path.split(path)

    pattern = r'^(.+)\s-\s(.+)\.(\w+)'
    match = re.match(pattern, file)
    if not match:
        return None

    title = match.group(1)
    author = match.group(2)
    author = re.sub(r'\[[^]]*]', '', author).strip()
    author = re.sub(r'\([^]]*\)', '', author)
    author = re.sub(r'（[^]]*）', '', author)

    alias = []
    if os.path.exists(os.path.join(root, 'alias.txt')):
        with open(os.path.join(root, 'alias.txt'), 'r') as f:
            alias = f.readlines()

    return LocalBook(title, alias, author)


def crawl_local(book_folder: str) -> list[LocalBook]:
    return file_utils.mapping_file_to_object(book_folder, file_filter, process_file)
