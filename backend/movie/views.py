"""Movie HTTP endpoints (thin: all work lives in :mod:`movie.services`)."""
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from movie import services


class DoubanDiffView(APIView):
    """``GET movie/douban250/diff`` — Douban Top 250 vs. local library."""

    def get(self, request):
        return Response(services.douban250_diff())


class CollectionCompleteView(APIView):
    """``GET movie/local/collection/complete`` — missing entries of owned TMDB sets."""

    def get(self, request):
        return Response(services.collection_complete())


def poster(request, image_path):
    """``GET movie/poster/<path>`` — stream a local poster image."""
    return serve_media_image(conf.MOVIE_ROOT, image_path, "poster")
