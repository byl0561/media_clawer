"""Movie HTTP endpoints (thin: all work lives in :mod:`movie.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from core.serializers import (
    AliasBindRequestSerializer,
    AliasBindResultSerializer,
    AliasTargetSerializer,
)
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


class AliasTargetsView(APIView):
    """All local movies the user may bind a missing rank entry to."""

    @extend_schema(
        responses=AliasTargetSerializer(many=True),
        operation_id="movies_alias_targets",
    )
    def get(self, request):
        return Response(services.alias_targets())


class AliasBindView(APIView):
    """Append rank titles as aliases on the chosen local movie."""

    @extend_schema(
        request=AliasBindRequestSerializer,
        responses=AliasBindResultSerializer,
        operation_id="movies_alias_bind",
    )
    def post(self, request):
        body = AliasBindRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        return Response(services.alias_bind(data["tmdb_id"], data["aliases"]))


def poster(request, image_path):
    """Stream a local poster image."""
    return serve_media_image(conf.MOVIE_ROOT, image_path, "poster")
