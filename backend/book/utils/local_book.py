import os
import re
import glob

from book.models.book import LocalBook
from constant import book_folder
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

    poster = None
    pattern = os.path.join(glob.escape(root), 'cover.*')
    cover_files = glob.glob(pattern)
    if len(cover_files) > 0:
        poster = cover_files[0].replace(book_folder, '')
        poster = f'/book/cover/{poster}'
    return LocalBook(title, alias, author, poster)


def crawl_local(book_folder: str) -> list[LocalBook]:
    return file_utils.mapping_file_to_object(book_folder, file_filter, process_file)
