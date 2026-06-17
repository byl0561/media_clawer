"""Movie diff use-cases.

Holds the logic that used to live in ``movie.views`` (crawl + diff + shape
the payload). The diff is recomputed on every request; only the upstream
Douban/TMDB responses stay cached (via :mod:`core.http`), which the cron job
keeps warm.
"""
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional

from core import conf
from core.exceptions import ShowNotFound, UpstreamUnavailable
from core.local_config import (
    add_aliases,
    add_skip_collection,
    read_config,
    read_root_excludes,
    set_skip_subtitle_check,
)
from core.matching import drop_excluded
from core.media_probe import VIDEO_EXTS, has_subtitle
from movie.crawlers.douban import crawl_douban_250
from movie.crawlers.local import crawl_local, file_filter
from movie.crawlers.tmdb import get_tmdb_movie, get_tmdb_movies_in_set
from movie.matching import get_extra_movies, get_missing_movies
from movie.models import Movie, MovieSet, TmdbMovie
from movie.serializers import MovieSerializer


def _is_retained(movie: Movie) -> bool:
    rate = movie.get_rate()
    # Matches TMDB's own /movie/top_rated cutoff (votes >= 300); score ≥ 7.0
    # keeps "decent" Top250 dropouts. Lower thresholds let lucky-high noise in.
    return rate.score > 7.0 and rate.votes > 300


_NO_SET = MovieSet(None, None, "TMDB")


def _enrich_local_movies(movies: list) -> None:
    """Replace each local movie's TMDB rate + collection with live ``/movie/{id}``.

    MoviePilot NFOs ship only a flat ``<rating>`` and no ``<set>`` /
    ``<uniqueid type="tmdbSet">``, and even tmm NFOs are scrape-time snapshots
    that drift from current TMDB. The diff is recomputed per request, so we
    always pull fresh — that way the retention threshold and the collection-
    tied carry-over both see the canonical current values regardless of NFO
    vintage. Cache-hit on the warm path since :func:`refresh_all` pre-warms.

    A collection id present in the local movie's ``skip_collections`` (set
    via ``POST /movies/ignore-collection``) is treated as no collection at
    all — junk TMDB groupings get silenced without affecting other movies.
    """
    for movie in movies:
        tmdb_movie = get_tmdb_movie(movie.tmdb_id)
        if tmdb_movie is None:
            continue
        movie.tmdb_rate = tmdb_movie.get_rate()
        new_set = tmdb_movie.move_set
        if new_set.set_id is not None and new_set.set_id in movie.skip_collections:
            new_set = _NO_SET
        movie.tmdb_set = new_set


def _local_movies() -> list:
    movies = crawl_local(conf.MOVIE_ROOT)
    _enrich_local_movies(movies)
    return movies


def _legal_movie(movie: TmdbMovie) -> bool:
    date_str = movie.get_date()
    if len(date_str) == 0:
        return False
    delta = datetime.today() - datetime.strptime(date_str, "%Y-%m-%d")
    return delta.days > 90


def _serialize(movies) -> list:
    return MovieSerializer(movies, many=True).data


def diff() -> dict:
    """Douban Top 250 vs. local library -> {"missing": [...], "extra": [...]}."""
    douban_movies = crawl_douban_250()
    if not douban_movies:
        raise UpstreamUnavailable()
    # Library-wide ignore list (<MOVIE_ROOT>/.mediaclawer.json -> exclude_titles):
    # drop ignored chart titles so they never surface as missing/extra.
    douban_movies = drop_excluded(douban_movies, read_root_excludes(conf.MOVIE_ROOT))
    local_movies = _local_movies()

    missing_movies = get_missing_movies(douban_movies, local_movies)
    extra_movies = get_extra_movies(douban_movies, local_movies)
    retained_set_names = {
        m.get_collection_name() for m in extra_movies if _is_retained(m)
    }
    visible_extra = [
        m
        for m in extra_movies
        if not _is_retained(m)
        and (
            m.get_collection_name() is None
            or m.get_collection_name() not in retained_set_names
        )
    ]
    return {
        "missing": _serialize(missing_movies),
        "extra": _serialize(visible_extra),
    }


def _weighted_score(rates) -> Optional[float]:
    """Vote-weighted average of TMDB scores, rounded to 1 decimal.

    ``sum(score*votes) / sum(votes)``. Members with 0 votes contribute
    nothing — a lone freshly-added entry can't drag the collection score.
    """
    total_votes = 0
    weighted = 0.0
    for r in rates:
        if r is None or r.votes <= 0:
            continue
        total_votes += r.votes
        weighted += r.score * r.votes
    if total_votes == 0:
        return None
    return round(weighted / total_votes, 1)


def series_gaps() -> list:
    """Owned TMDB collections with their local and missing members.

    Each entry returns the full collection picture so the frontend can render
    the left-stack/right-tile layout with a vote-weighted collection score:

      [{
          "collection_id": int,
          "collection_name": str,
          "score": float | None,   # weighted across every TMDB member
          "votes": int,            # sum of member votes
          "local":   [<movie>, ...],
          "missing": [<movie>, ...]
      }, ...]

    Collections with no missing members are dropped — there's nothing to
    surface.
    """
    local_movies = _local_movies()

    grouped: dict = {}
    for movie in local_movies:
        set_id = movie.tmdb_set.set_id
        if set_id is None:
            continue
        grouped.setdefault(set_id, []).append(movie)

    result = []
    for set_id, locals_ in grouped.items():
        members = get_tmdb_movies_in_set(set_id)
        if not members:
            continue
        local_ids = {m.tmdb_id for m in locals_}
        missing = [
            m for m in members if m.tmdb_id not in local_ids and _legal_movie(m)
        ]
        if not missing:
            continue

        member_rates = [m.get_rate() for m in members]
        result.append(
            {
                "collection_id": set_id,
                "collection_name": members[0].move_set.name,
                "score": _weighted_score(member_rates),
                "votes": sum((r.votes for r in member_rates if r is not None), 0),
                "local": _serialize(locals_),
                "missing": _serialize(missing),
            }
        )
    result.sort(key=lambda x: x["collection_name"] or "")
    return result


def refresh_all() -> None:
    """Repopulate the upstream Douban / TMDB caches (used by cron)."""
    crawl_douban_250(cache=False)
    movies = crawl_local(conf.MOVIE_ROOT)
    for m in movies:
        get_tmdb_movie(m.tmdb_id, cache=False)
    _enrich_local_movies(movies)
    set_ids = {m.tmdb_set.set_id for m in movies if m.tmdb_set.set_id is not None}
    for set_id in set_ids:
        get_tmdb_movies_in_set(set_id, cache=False)


# --- Alias bind (manual chinese-title supplement) -----------------------
# See tvshow.services for the design rationale. Movies use the same flow:
# locate the on-disk folder by TMDB id, append rank titles to the folder's
# ``.mediaclawer.json`` ``aliases`` so the next list/local diff text-matches them.


def _find_movie_dir(tmdb_id: int) -> Optional[str]:
    """Directory of the movie nfo whose tmdb ``uniqueid`` == ``tmdb_id``.

    ``file_filter`` accepts both tmm's ``movie.nfo`` and MoviePilot's
    ``{title} ({year}).nfo``, so this works on mixed libraries.
    """
    base = os.path.realpath(conf.MOVIE_ROOT)
    if not os.path.isdir(base):
        return None
    for current, _dirs, files in os.walk(base):
        for fname in files:
            if not file_filter(fname):
                continue
            try:
                tree = ET.parse(os.path.join(current, fname))
                node = tree.getroot().find("./uniqueid[@type='tmdb']")
                if node is not None and node.text and int(node.text) == tmdb_id:
                    return current
            except (ET.ParseError, ValueError, TypeError):
                continue
    return None


def alias_targets() -> list:
    """All local movies usable as bind targets for a missing rank item."""
    targets = []
    for local in crawl_local(conf.MOVIE_ROOT):  # no enrichment needed; only metadata read
        targets.append(
            {
                "tmdb_id": local.tmdb_id,
                "title": local.title,
                "year": local.year,
                "poster": local.poster,
            }
        )
    targets.sort(key=lambda x: x["title"] or "")
    return targets


def _folder_has_subtitle(folder: str) -> bool:
    """Folder counts as 'has subtitle' if at least one video in it carries one.

    Movie folders typically hold one video plus optional extras (trailers,
    behind-the-scenes); treating any present subtitle on any video as
    sufficient matches what the user means by "this movie has a subtitle".

    Returns False when the folder has no video files at all — an NFO'd movie
    with the media missing is itself a gap and should land in the subtitle
    list (user can clean up the empty NFO or re-acquire the file).
    """
    try:
        names = os.listdir(folder)
    except OSError:
        return True
    for name in names:
        if os.path.splitext(name)[1].lower() not in VIDEO_EXTS:
            continue
        if has_subtitle(os.path.join(folder, name)):
            return True
    return False


def warm_subtitle_cache() -> None:
    """Pre-walk every local movie so the subtitle probe cache is hot.

    Just calls :func:`subtitle_gaps` and discards the response — the side
    effect (populating ``media_probe``'s per-file Redis cache) is what
    matters, so the first user-facing /movies/subtitle-gaps doesn't pay
    the per-video ffprobe cost.
    """
    subtitle_gaps()


def subtitle_gaps() -> list:
    """Local movies missing both external and embedded subtitles."""
    result = []
    for movie in crawl_local(conf.MOVIE_ROOT):
        if not movie.path:
            continue
        cfg = read_config(movie.path)
        if cfg.get("skip_subtitle_check"):
            continue
        if _folder_has_subtitle(movie.path):
            continue
        result.append(movie)
    result.sort(key=lambda m: (m.title or "").lower())
    return _serialize(result)


def ignore_subtitle(tmdb_id: int) -> dict:
    """Set ``skip_subtitle_check: true`` on the movie's ``.mediaclawer.json``."""
    base = os.path.realpath(conf.MOVIE_ROOT)
    movie_dir = _find_movie_dir(tmdb_id)
    if movie_dir is None:
        raise ShowNotFound()
    target = os.path.realpath(movie_dir)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()
    return {"updated": set_skip_subtitle_check(target)}


def ignore_collection(collection_id: int) -> dict:
    """Mark ``collection_id`` as ignored on every local movie that's in it.

    The new ``skip_collections`` entry lands in each affected movie's
    ``.mediaclawer.json``; the next diff drops the TMDB collection for those
    movies (see :func:`_enrich_local_movies`). Idempotent — already-ignored
    movies aren't double-counted.
    """
    base = os.path.realpath(conf.MOVIE_ROOT)
    updated = 0
    # Use enriched locals so MoviePilot NFOs (which omit <set>) still match —
    # the live TMDB lookup fills set_id. Already-ignored movies are no-ops
    # because the enrichment clears their tmdb_set down to None.
    for movie in _local_movies():
        if movie.tmdb_set.set_id != collection_id:
            continue
        if not movie.path:
            continue
        target = os.path.realpath(movie.path)
        if target != base and not target.startswith(base + os.sep):
            continue
        if add_skip_collection(target, collection_id):
            updated += 1
    return {"updated": updated}


def alias_bind(tmdb_id: int, aliases: List[str]) -> dict:
    """Append ``aliases`` to the movie's ``.mediaclawer.json``."""
    base = os.path.realpath(conf.MOVIE_ROOT)
    movie_dir = _find_movie_dir(tmdb_id)
    if movie_dir is None:
        raise ShowNotFound()

    target = os.path.realpath(movie_dir)
    if target != base and not target.startswith(base + os.sep):
        raise ShowNotFound()

    added = add_aliases(target, aliases)
    return {"bound": True, "added": added}
