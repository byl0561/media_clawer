"""Centralised configuration for the crawler/diff pipeline.

Reads directly from os.environ so this module has no framework dependency.
"""
import os
from typing import Tuple

# --- HTTP scraping -------------------------------------------------------
USER_AGENT: str = os.environ.get(
    "CRAWLER_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
)
DOUBAN_COOKIE: str = os.environ.get("DOUBAN_COOKIE", "")
TMDB_API_KEY: str = os.environ.get("TMDB_API_KEY", "")

TMDB_IMAGE_PATH = "https://image.tmdb.org/t/p/original"
TMDB_MOVIE_PATH = "https://www.themoviedb.org/movie"
TMDB_TV_PATH = "https://www.themoviedb.org/tv"
BANGUMI_ANIME_PATH = "https://bangumi.tv/subject"

# --- Local media libraries -----------------------------------------------
MEDIA_ROOTS: dict = {
    "movie": os.environ.get("MOVIE_FOLDER", "/Volumes/Movie/"),
    "tv": os.environ.get("TV_FOLDER", "/Volumes/TV/"),
    "anime": os.environ.get("ANIME_FOLDER", "/Volumes/Anime/"),
    "music": os.environ.get("MUSIC_FOLDER", "/Volumes/Music/"),
    "book": os.environ.get("BOOK_FOLDER", "/Volumes/Book/"),
}

MOVIE_ROOT: str = MEDIA_ROOTS["movie"]
TV_ROOT: str = MEDIA_ROOTS["tv"]
ANIME_ROOT: str = MEDIA_ROOTS["anime"]
MUSIC_ROOT: str = MEDIA_ROOTS["music"]
BOOK_ROOT: str = MEDIA_ROOTS["book"]

# --- Tuning knobs --------------------------------------------------------
HTTP_TIMEOUT: Tuple[int, int] = (5, int(os.environ.get("HTTP_READ_TIMEOUT", "30")))
SCAN_WORKERS: int = int(
    os.environ.get("SCAN_WORKERS", str(min(8, os.cpu_count() or 4)))
)
TMDB_MAX_RETRIES: int = int(os.environ.get("TMDB_MAX_RETRIES", "3"))
SOURCE_CACHE_TTL_MINUTES: int = int(
    os.environ.get("SOURCE_CACHE_TTL_MINUTES", str(60 * 24 * 8))
)
