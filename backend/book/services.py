"""Book diff use-case (logic moved out of the old ``book.views``).

Recomputed every request; only the upstream Douban response stays cached
(via :mod:`core.http`), kept warm by cron. ``_is_retained_book`` is kept as
the original unconditional ``True`` (so ``extra`` stays empty) to preserve
the diff semantics exactly.
"""
from core import conf
from core.exceptions import UpstreamUnavailable
from book.crawlers.douban import crawl_douban_250
from book.crawlers.local import crawl_local
from book.matching import get_missing_books
from book.models import Book
from book.serializers import BookSerializer


def _is_retained_book(book: Book) -> bool:
    return True


def _serialize(books) -> list:
    return BookSerializer(books, many=True).data


def diff() -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    douban_books = crawl_douban_250()
    if not douban_books:
        raise UpstreamUnavailable()
    local_books = crawl_local(conf.BOOK_ROOT)
    missing_books = get_missing_books(douban_books, local_books)
    extra_books = get_missing_books(local_books, douban_books)
    return {
        "missing": _serialize(missing_books),
        "extra": _serialize([b for b in extra_books if not _is_retained_book(b)]),
    }


def refresh_all() -> None:
    """Repopulate the upstream Douban cache (used by cron)."""
    crawl_douban_250(cache=False)
