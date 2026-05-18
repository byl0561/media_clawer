"""TV/anime HTTP endpoints (thin: work lives in :mod:`tvshow.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from tvshow import services
from tvshow.serializers import LocalGapSerializer, ShowDiffSerializer


class TvDiffView(APIView):
    """Douban TV doulists vs. the local TV library."""

    @extend_schema(responses=ShowDiffSerializer, operation_id="tv_shows_diff")
    def get(self, request):
        return Response(services.tv_diff())


class AnimeDiffView(APIView):
    """Bangumi TV ranking vs. the local anime library."""

    @extend_schema(responses=ShowDiffSerializer, operation_id="anime_diff")
    def get(self, request):
        return Response(services.anime_diff())


class TvLocalGapsView(APIView):
    """Local TV shows missing whole seasons and/or behind on episodes."""

    @extend_schema(
        responses=LocalGapSerializer(many=True), operation_id="tv_shows_local_gaps"
    )
    def get(self, request):
        return Response(services.local_gaps("tv"))


class AnimeLocalGapsView(APIView):
    """Local anime missing whole seasons and/or behind on episodes."""

    @extend_schema(
        responses=LocalGapSerializer(many=True), operation_id="anime_local_gaps"
    )
    def get(self, request):
        return Response(services.local_gaps("anime"))


def tv_poster(request, image_path):
    return serve_media_image(conf.TV_ROOT, image_path, "poster")


def anime_poster(request, image_path):
    return serve_media_image(conf.ANIME_ROOT, image_path, "poster")
