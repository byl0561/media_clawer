"""Centralised configuration for the crawler/diff pipeline.

Everything that used to live in the project-root ``constant.py`` module now
comes from Django settings (which read the environment once at startup), so
configuration has a single source of truth and is overridable per deployment.
"""
from django.conf import settings

# --- HTTP scraping -------------------------------------------------------
USER_AGENT: str = settings.CRAWLER_USER_AGENT
DOUBAN_COOKIE: str = settings.DOUBAN_COOKIE
TMDB_API_KEY: str = settings.TMDB_API_KEY

# Static third-party URL fragments (not environment dependent).
TMDB_IMAGE_PATH = "https://image.tmdb.org/t/p/original"
TMDB_MOVIE_PATH = "https://www.themoviedb.org/movie"
TMDB_TV_PATH = "https://www.themoviedb.org/tv"
BANGUMI_ANIME_PATH = "https://bangumi.tv/subject"

# --- Local media libraries ----------------------------------------------
# Mapping of logical library name -> absolute folder (kept with a trailing
# separator so the existing ``path.replace(root, "")`` poster-URL logic keeps
# producing byte-identical results).
MEDIA_ROOTS: dict = settings.MEDIA_LIBRARY_ROOTS

MOVIE_ROOT: str = MEDIA_ROOTS["movie"]
TV_ROOT: str = MEDIA_ROOTS["tv"]
ANIME_ROOT: str = MEDIA_ROOTS["anime"]
MUSIC_ROOT: str = MEDIA_ROOTS["music"]
BOOK_ROOT: str = MEDIA_ROOTS["book"]

# --- Tuning knobs --------------------------------------------------------
# (connect, read) timeout for every outbound HTTP request; without this a
# hung upstream would block a worker thread forever.
HTTP_TIMEOUT = settings.HTTP_REQUEST_TIMEOUT
SCAN_WORKERS: int = settings.SCAN_WORKER_COUNT

# Raw upstream responses (HTML / TMDB JSON) cache TTL. The computed diff is
# recomputed per request and is intentionally not cached.
SOURCE_CACHE_TTL_MINUTES: int = settings.SOURCE_CACHE_TTL_MINUTES
