"""TV/anime HTTP endpoints (thin: work lives in :mod:`tvshow.services`)."""
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from tvshow import services


class DoubanDiffView(APIView):
    """``GET tv/douban100/diff``."""

    def get(self, request):
        return Response(services.douban100_diff())


class BangumiDiffView(APIView):
    """``GET anime/bangumi/diff``."""

    def get(self, request):
        return Response(services.bangumi_diff())


class TvSeasonMissingView(APIView):
    """``GET tv/local/season/missing``."""

    def get(self, request):
        return Response(services.season_missing("tv"))


class TvEpisodeMissingView(APIView):
    """``GET tv/local/episode/missing``."""

    def get(self, request):
        return Response(services.episode_missing("tv"))


class AnimeSeasonMissingView(APIView):
    """``GET anime/local/season/missing``."""

    def get(self, request):
        return Response(services.season_missing("anime"))


class AnimeEpisodeMissingView(APIView):
    """``GET anime/local/episode/missing``."""

    def get(self, request):
        return Response(services.episode_missing("anime"))


def tv_poster(request, image_path):
    return serve_media_image(conf.TV_ROOT, image_path, "poster")


def anime_poster(request, image_path):
    return serve_media_image(conf.ANIME_ROOT, image_path, "poster")
