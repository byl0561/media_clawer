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

            title = match.group(1)
            author = match.group(2)
            author = re.sub(r'\[[^]]*]', '', author)
            books.append(LocalBook(title, author))
    return books
