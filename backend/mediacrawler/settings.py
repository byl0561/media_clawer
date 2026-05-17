"""Django settings for the mediacrawler project.

All deployment-specific values are read from the environment here so the rest
of the codebase can depend on :mod:`core.conf` instead of reading os.environ
in scattered import-time module globals.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: str = "False") -> bool:
    return os.environ.get(name, default).lower() == "true"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# --- Core security ------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-f(^-ob0h9b(b*072xyh@ux$u6+d8dbi8b*aj$-l*)a!n1_kz0@",
)
DEBUG = _env_bool("DEBUG")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# --- Applications -------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_crontab",
    "movie.apps.MovieConfig",
    "tvshow.apps.TvshowConfig",
    "music.apps.MusicConfig",
    "book.apps.BookConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mediacrawler.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mediacrawler.wsgi.application"

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cache (Redis) ------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://%s:%s"
        % (os.environ.get("REDIS_HOST", ""), os.environ.get("REDIS_PORT", "6379")),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.environ.get("REDIS_PASS", ""),
        },
    },
}

# --- Django REST Framework ---------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        ["rest_framework.renderers.JSONRenderer"]
        + (["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else [])
    ),
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

# --- Crawler / diff pipeline configuration (consumed via core.conf) ------
CRAWLER_USER_AGENT = os.environ.get(
    "CRAWLER_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
)
DOUBAN_COOKIE = os.environ.get("DOUBAN_COOKIE", "")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")

# Trailing separator is intentional: poster URLs are derived via
# ``path.replace(root, "")`` and must stay byte-identical.
MEDIA_LIBRARY_ROOTS = {
    "movie": os.environ.get("MOVIE_FOLDER", "/Volumes/Movie/"),
    "tv": os.environ.get("TV_FOLDER", "/Volumes/TV/"),
    "anime": os.environ.get("ANIME_FOLDER", "/Volumes/Anime/"),
    "music": os.environ.get("MUSIC_FOLDER", "/Volumes/Music/"),
    "book": os.environ.get("BOOK_FOLDER", "/Volumes/Book/"),
}

# (connect, read) seconds — bounds every outbound scrape/API call.
HTTP_REQUEST_TIMEOUT = (5, _env_int("HTTP_READ_TIMEOUT", 30))
SCAN_WORKER_COUNT = _env_int("SCAN_WORKERS", min(8, (os.cpu_count() or 4)))
# Upstream Douban/TMDB responses are cached this long; cron pre-warms them.
# The computed diff itself is NOT cached — it is recomputed on every request.
# 8 days (> the weekly cron interval) so the upstream cache never expires
# between cron refreshes, even at the boundary.
SOURCE_CACHE_TTL_MINUTES = _env_int("SOURCE_CACHE_TTL_MINUTES", 60 * 24 * 8)

# --- Logging ------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# --- Scheduled cache pre-warming ---------------------------------------
CRONJOBS = [
    ("30 4 * * 1", "book.cron.cronjob"),
    ("30 4 * * 2", "movie.cron.cronjob"),
    ("30 4 * * 3", "music.cron.cronjob"),
    ("30 4 * * 4", "tvshow.cron.cronjob"),
]
