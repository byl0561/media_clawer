"""Local book scanner ("{title} - {author}.{ext}" files). Rules unchanged."""
import glob
import os
import re

from core import conf, scanning
from book.models import LocalBook

_FILE_PATTERN = re.compile(r"^(.+)\s-\s(.+)\.(\w+)")


def file_filter(file: str) -> bool:
    return _FILE_PATTERN.match(file) is not None


def process_file(path: str):
    root, file = os.path.split(path)

    match = _FILE_PATTERN.match(file)
    if not match:
        return None

    title = match.group(1)
    author = match.group(2)
    author = re.sub(r"\[[^]]*]", "", author).strip()
    author = re.sub(r"\([^]]*\)", "", author)
    author = re.sub(r"（[^]]*）", "", author)

    alias = []
    if os.path.exists(os.path.join(root, "alias.txt")):
        with open(os.path.join(root, "alias.txt"), "r") as f:
            alias = f.readlines()

    poster = None
    cover_files = glob.glob(os.path.join(glob.escape(root), "cover.*"))
    if len(cover_files) > 0:
        poster = "/book/cover/" + cover_files[0].replace(conf.BOOK_ROOT, "")

    return LocalBook(title, alias, author, poster)


def crawl_local(root: str) -> list:
    return scanning.scan_files(root, file_filter, process_file)
