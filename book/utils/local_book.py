import os
import re

from book.models.book import LocalBook


def crawl_local(book_folder: str) -> list[LocalBook]:
    books = []

    pattern = r'^(.+)\s-\s(.+)\.(\w+)'
    for root, dirs, files in os.walk(book_folder):
        for file in files:
            match = re.match(pattern, file)
            if not match:
                continue

            titles = match.group(1)
            author = match.group(2)
            author = re.sub(r'\[[^]]*]', '', author).strip()
            author = re.sub(r'\([^]]*\)', '', author)
            author = re.sub(r'（[^]]*）', '', author)
            books.append(LocalBook(titles, author))
    return books
