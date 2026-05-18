"""Book similarity rules (logic identical to the original ``utils.common``).

Book title normalisation uses ``[^]]`` parenthesis patterns (slightly
different from the other domains), so the regexes are kept verbatim here
rather than via the shared ``core.matching`` helper.
"""
import re

from core.matching import find_missing, title_ratio
from book.models import Book

_PAREN_ASCII = re.compile(r"\([^]]*\)")
_PAREN_CJK = re.compile(r"（[^]]*）")


def _normalize(name: str) -> str:
    name = _PAREN_ASCII.sub("", name)
    name = _PAREN_CJK.sub("", name)
    return name.replace("全集", "")


def book_similarity(book1: Book, book2: Book) -> bool:
    for name1 in book1.get_titles():
        for name2 in book2.get_titles():
            if title_ratio(_normalize(name1), _normalize(name2)) > 0.8:
                return True
    return False


def get_missing_books(target_books: list, compare_books: list) -> list:
    return find_missing(target_books, compare_books, book_similarity)
