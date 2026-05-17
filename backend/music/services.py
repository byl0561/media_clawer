"""Album diff use-case (logic moved out of the old ``music.views``).

Recomputed every request; only the upstream Douban response stays cached
(via :mod:`core.http`), kept warm by cron.
"""
from core import conf
from core.exceptions import UpstreamUnavailable
from music.crawlers.douban import crawl_douban_250
from music.crawlers.local import crawl_local
from music.matching import get_missing_albums
from music.serializers import AlbumSerializer


def _serialize(albums) -> list:
    return AlbumSerializer(albums, many=True).data


def diff() -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    douban_albums = crawl_douban_250()
    if not douban_albums:
        raise UpstreamUnavailable()
    local_albums = crawl_local(conf.MUSIC_ROOT)
    return {
        "missing": _serialize(get_missing_albums(douban_albums, local_albums)),
        "extra": _serialize(get_missing_albums(local_albums, douban_albums)),
    }


def refresh_all() -> None:
    """Repopulate the upstream Douban cache (used by cron)."""
    crawl_douban_250(cache=False)
