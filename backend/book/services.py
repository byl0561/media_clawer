"""Book diff use-case — fully async."""
import asyncio
import os
from typing import List

from core import conf
from core.local_config import add_aliases, read_root_excludes
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.identifiers import decode_local_path, encode_local_path
from book.crawlers.douban import crawl_douban_250
from book.crawlers.local import crawl_local
from book.matching import get_missing_books
from book.models import Book

_BOOK_DEFAULT_EXCLUDES = ["中国少年儿童百科全书", "十万个为什么"]


def _book_excludes() -> List[str]:
    return _BOOK_DEFAULT_EXCLUDES + read_root_excludes(conf.BOOK_ROOT)


def _is_retained_book(book: Book) -> bool:
    return True


def _book_to_dict(obj) -> dict:
    titles = obj.get_titles()
    rate = obj.get_rate()
    return {
        "title": titles[0] if titles else "",
        "score": round(rate.score, 1) if rate is not None else None,
        "votes": rate.votes if rate is not None else None,
        "poster": obj.get_poster(),
        "link": obj.get_link(),
        "author": obj.get_author(),
    }


def _serialize(books) -> list:
    return [_book_to_dict(b) for b in books]


async def diff(sink=None) -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    if sink:
        await sink.report("正在爬取豆瓣书单…", 5)
    loop = asyncio.get_running_loop()
    douban_books, local_books = await asyncio.gather(
        crawl_douban_250(exclude_titles=_book_excludes()),
        loop.run_in_executor(None, crawl_local, conf.BOOK_ROOT),
    )
    if not douban_books:
        raise UpstreamUnavailable()
    missing_books = get_missing_books(douban_books, local_books)
    extra_books = get_missing_books(local_books, douban_books)
    return {
        "missing": _serialize(missing_books),
        "extra": _serialize([b for b in extra_books if not _is_retained_book(b)]),
    }


async def refresh_all() -> None:
    """Repopulate the upstream Douban cache (used by cron)."""
    await crawl_douban_250(cache=False, exclude_titles=_book_excludes())


def alias_targets() -> list:
    targets = []
    for local in crawl_local(conf.BOOK_ROOT):
        if not local.path:
            continue
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

    added = add_aliases(target, aliases)
    return {"bound": True, "added": added}
