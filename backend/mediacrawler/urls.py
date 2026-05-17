"""URL routing for the mediacrawler project.

Paths and response shapes are intentionally identical to the pre-refactor API
so the existing Vue frontend keeps working unchanged. Cross-app path scheme
(``anime/*`` is served by the ``tvshow`` app against the anime library) is
preserved, so routing is kept centralised here rather than per-app.
"""
from django.urls import path

from book import views as book_views
from movie import views as movie_views
from music import views as music_views
from tvshow import views as tv_views

urlpatterns = [
    # Movie
    path(
        "movie/douban250/diff",
        movie_views.DoubanDiffView.as_view(),
        name="movie-douban250-diff",
    ),
    path(
        "movie/local/collection/complete",
        movie_views.CollectionCompleteView.as_view(),
        name="movie-collection-complete",
    ),
    path("movie/poster/<path:image_path>", movie_views.poster, name="movie-poster"),
    # TV
    path(
        "tv/douban100/diff",
        tv_views.DoubanDiffView.as_view(),
        name="tv-douban100-diff",
    ),
    path(
        "tv/local/season/missing",
        tv_views.TvSeasonMissingView.as_view(),
        name="tv-season-missing",
    ),
    path(
        "tv/local/episode/missing",
        tv_views.TvEpisodeMissingView.as_view(),
        name="tv-episode-missing",
    ),
    path("tv/poster/<path:image_path>", tv_views.tv_poster, name="tv-poster"),
    # Anime (served by the tvshow app)
    path(
        "anime/bangumi/diff",
        tv_views.BangumiDiffView.as_view(),
        name="anime-bangumi-diff",
    ),
    path(
        "anime/local/season/missing",
        tv_views.AnimeSeasonMissingView.as_view(),
        name="anime-season-missing",
    ),
    path(
        "anime/local/episode/missing",
        tv_views.AnimeEpisodeMissingView.as_view(),
        name="anime-episode-missing",
    ),
    path(
        "anime/poster/<path:image_path>",
        tv_views.anime_poster,
        name="anime-poster",
    ),
    # Album
    path(
        "album/douban250/diff",
        music_views.DoubanDiffView.as_view(),
        name="album-douban250-diff",
    ),
    path("album/cover/<path:image_path>", music_views.cover, name="album-cover"),
    # Book
    path(
        "book/douban250/diff",
        book_views.DoubanDiffView.as_view(),
        name="book-douban250-diff",
    ),
    path("book/cover/<path:image_path>", book_views.cover, name="book-cover"),
]
