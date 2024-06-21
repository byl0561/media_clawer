import difflib
import re

from book.models.book import *


def book_similarity(book1: Book, book2: Book) -> bool:
    book1_names = book1.get_titles()
    book1_author = book1.get_author()

    book2_names = book2.get_titles()
    book2_author = book2.get_author()

    if difflib.SequenceMatcher(None, book1_author, book2_author).ratio() <= 0.4:
        return False

    for book1_name in book1_names:
        for book2_name in book2_names:
            book1_name = re.sub(r'\([^]]*\)', '', book1_name)
            book1_name = re.sub(r'（[^]]*）', '', book1_name)
            book2_name = re.sub(r'\([^]]*\)', '', book2_name)
            book2_name = re.sub(r'（[^]]*）', '', book2_name)
            if difflib.SequenceMatcher(None, book1_name, book2_name).ratio() > 0.8:
                return True

    return False


def get_missing_books(target_books: list[Book], compare_books: list[Book]) -> list[Book]:
    missing_books = []

    for target_book in target_books:
        found = False
        for compare_book in compare_books:
            if book_similarity(target_book, compare_book):
                found = True
                break
        if not found:
            missing_books.append(target_book)

    return missing_books