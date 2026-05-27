"""Book diff use-case (logic moved out of the old ``book.views``).

Recomputed every request; only the upstream Douban response stays cached
(via :mod:`core.http`), kept warm by cron. ``_is_retained_book`` is kept as
the original unconditional ``True`` (so ``extra`` stays empty) to preserve
the diff semantics exactly.
"""
import os
from typing import List

from core import conf
from core.aliases import append_unique_aliases
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.identifiers import decode_local_path, encode_local_path
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


# --- Alias bind (manual chinese-title supplement) -----------------------
# Book entries have no public unique key; same signed-token flow as albums.


def alias_targets() -> list:
    """All local books usable as bind targets for a missing rank item."""
    targets = []
    for local in crawl_local(conf.BOOK_ROOT):
        if not local.path:
            continue
        # LocalBook.titles 是按 "_" split 的，取第 0 个作为展示标题
        display_title = local.titles[0] if local.titles else ""
        targets.append(
            {
                "token": encode_local_path(local.path),
                "title": display_title,
                "author": local.author,
                "poster": local.poster,
            }
        )
    targets.sort(key=lambda x: x["title"] or "")
    return targets


def alias_bind(token: str, aliases: List[str]) -> dict:
    """Append ``aliases`` to the matched book's ``alias.txt``."""
    try:
        path = decode_local_path(token)
    except ValueError as exc:
        raise ShowNotFound() from exc

    base = os.path.realpath(conf.BOOK_ROOT)
    target = os.path.realpath(path)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()
    if not os.path.isdir(target):
        raise ShowNotFound()

    added = append_unique_aliases(target, aliases)
    return {"bound": True, "added": added}
