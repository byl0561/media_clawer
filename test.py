import os
import re

import utils.file_utils as file_utils
from book.models.book import LocalBook


def file_filter(file:str) -> bool:
    pattern = r'^(.+)\s-\s(.+)\.(\w+)'
    return re.match(pattern, file) is not None

def process_file(path:str):
    _, file = os.path.split(path)

    pattern = r'^(.+)\s-\s(.+)\.(\w+)'
    match = re.match(pattern, file)
    if match:
        title = match.group(1)
        author = match.group(2)
        author = re.sub(r'\[[^]]*]', '', author).strip()
        author = re.sub(r'\([^]]*\)', '', author)
        author = re.sub(r'（[^]]*）', '', author)
        return LocalBook(title, author)
    return None

def main():

    root_directory = '/Volumes/Book'
    books = file_utils.mapping_file_to_object(root_directory, file_filter, process_file)
    print(books)


if __name__ == "__main__":
    main()