"""URL routing for the mediacrawler project.

RESTful, versioned API. Nginx proxies ``/api/`` to Django with the prefix
stripped, so an external ``GET /api/v1/movies/diff`` arrives here as
``v1/movies/diff``. ``anime`` is a first-class resource even though it is
served by the ``tvshow`` app against the anime library root.
"""
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from book import views as book_views
from core import views as core_views
from movie import views as movie_views
from music import views as music_views
from tvshow import views as tv_views

urlpatterns = [
    # Movies
    path("v1/movies/diff", movie_views.DiffView.as_view(), name="movies-diff"),
    path(
        "v1/movies/collection-gaps",
        movie_views.CollectionGapsView.as_view(),
        name="movies-collection-gaps",
    ),
    path(
        "v1/movies/poster/<path:image_path>",
        movie_views.poster,
        name="movies-poster",
    ),
    path(
        "v1/movies/alias-targets",
        movie_views.AliasTargetsView.as_view(),
        name="movies-alias-targets",
    ),
    path(
        "v1/movies/alias-bind",
        movie_views.AliasBindView.as_view(),
        name="movies-alias-bind",
    ),
    # TV shows
    path("v1/tv-shows/diff", tv_views.TvDiffView.as_view(), name="tv-shows-diff"),
    path(
        "v1/tv-shows/local-gaps",
        tv_views.TvLocalGapsView.as_view(),
        name="tv-shows-local-gaps",
    ),
    path(
        "v1/tv-shows/poster/<path:image_path>",
        tv_views.tv_poster,
        name="tv-shows-poster",
    ),
    path(
        "v1/tv-shows/ignore-options",
        tv_views.TvIgnoreOptionsView.as_view(),
        name="tv-shows-ignore-options",
    ),
    path(
        "v1/tv-shows/ignore",
        tv_views.TvIgnoreView.as_view(),
        name="tv-shows-ignore",
    ),
    path(
        "v1/tv-shows/alias-targets",
        tv_views.TvAliasTargetsView.as_view(),
        name="tv-shows-alias-targets",
    ),
    path(
        "v1/tv-shows/alias-bind",
        tv_views.TvAliasBindView.as_view(),
        name="tv-shows-alias-bind",
    ),
    # Anime (served by the tvshow app)
    path("v1/anime/diff", tv_views.AnimeDiffView.as_view(), name="anime-diff"),
    path(
        "v1/anime/local-gaps",
        tv_views.AnimeLocalGapsView.as_view(),
        name="anime-local-gaps",
    ),
    path(
        "v1/anime/poster/<path:image_path>",
        tv_views.anime_poster,
        name="anime-poster",
    ),
    path(
        "v1/anime/ignore-options",
        tv_views.AnimeIgnoreOptionsView.as_view(),
        name="anime-ignore-options",
    ),
    path(
        "v1/anime/ignore",
        tv_views.AnimeIgnoreView.as_view(),
        name="anime-ignore",
    ),
    path(
        "v1/anime/alias-targets",
        tv_views.AnimeAliasTargetsView.as_view(),
        name="anime-alias-targets",
    ),
    path(
        "v1/anime/alias-bind",
        tv_views.AnimeAliasBindView.as_view(),
        name="anime-alias-bind",
    ),
    # Albums
    path("v1/albums/diff", music_views.DiffView.as_view(), name="albums-diff"),
    path(
        "v1/albums/cover/<path:image_path>",
        music_views.cover,
        name="albums-cover",
    ),
    path(
        "v1/albums/alias-targets",
        music_views.AliasTargetsView.as_view(),
        name="albums-alias-targets",
    ),
    path(
        "v1/albums/alias-bind",
        music_views.AliasBindView.as_view(),
        name="albums-alias-bind",
    ),
    # Books
    path("v1/books/diff", book_views.DiffView.as_view(), name="books-diff"),
    path(
        "v1/books/cover/<path:image_path>",
        book_views.cover,
        name="books-cover",
    ),
    path(
        "v1/books/alias-targets",
        book_views.AliasTargetsView.as_view(),
        name="books-alias-targets",
    ),
    path(
        "v1/books/alias-bind",
        book_views.AliasBindView.as_view(),
        name="books-alias-bind",
    ),
    # Remote poster/cover proxy (replaces client-side images.weserv.nl)
    path("v1/images/proxy", core_views.image_proxy, name="image-proxy"),
    # OpenAPI schema + Swagger UI
    path("v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs",
    ),
]
