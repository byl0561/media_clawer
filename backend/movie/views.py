"""Movie HTTP endpoints (thin: all work lives in :mod:`movie.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from movie import services
from movie.serializers import MovieCollectionGapSerializer, MovieDiffSerializer


class DiffView(APIView):
    """Douban Top 250 vs. the local movie library."""

    @extend_schema(responses=MovieDiffSerializer, operation_id="movies_diff")
    def get(self, request):
        return Response(services.diff())


class CollectionGapsView(APIView):
    """Owned TMDB collections that still have entries missing locally."""

    @extend_schema(
        responses=MovieCollectionGapSerializer(many=True),
        operation_id="movies_collection_gaps",
    )
    def get(self, request):
        return Response(services.collection_gaps())


def poster(request, image_path):
    """Stream a local poster image."""
    return serve_media_image(conf.MOVIE_ROOT, image_path, "poster")
