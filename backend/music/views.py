"""Album HTTP endpoints (thin: work lives in :mod:`music.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from core.serializers import (
    AlbumAliasTargetSerializer,
    AliasBindResultSerializer,
    TokenAliasBindRequestSerializer,
)
from music import services
from music.serializers import AlbumDiffSerializer


class DiffView(APIView):
    """Douban Top 250 albums vs. the local album library."""

    @extend_schema(responses=AlbumDiffSerializer, operation_id="albums_diff")
    def get(self, request):
        return Response(services.diff())


class AliasTargetsView(APIView):
    """All local albums usable as bind targets for a missing rank entry."""

    @extend_schema(
        responses=AlbumAliasTargetSerializer(many=True),
        operation_id="albums_alias_targets",
    )
    def get(self, request):
        return Response(services.alias_targets())


class AliasBindView(APIView):
    """Append rank titles as aliases on the chosen local album (token-keyed)."""

    @extend_schema(
        request=TokenAliasBindRequestSerializer,
        responses=AliasBindResultSerializer,
        operation_id="albums_alias_bind",
    )
    def post(self, request):
        body = TokenAliasBindRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        return Response(services.alias_bind(data["token"], data["aliases"]))


def cover(request, image_path):
    """Stream a local album cover."""
    return serve_media_image(conf.MUSIC_ROOT, image_path, "cover")
