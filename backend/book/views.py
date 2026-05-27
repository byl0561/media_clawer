"""Book HTTP endpoints (thin: work lives in :mod:`book.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from core.serializers import (
    AliasBindResultSerializer,
    BookAliasTargetSerializer,
    TokenAliasBindRequestSerializer,
)
from book import services
from book.serializers import BookDiffSerializer


class DiffView(APIView):
    """Douban Top 250 books vs. the local book library."""

    @extend_schema(responses=BookDiffSerializer, operation_id="books_diff")
    def get(self, request):
        return Response(services.diff())


class AliasTargetsView(APIView):
    """All local books usable as bind targets for a missing rank entry."""

    @extend_schema(
        responses=BookAliasTargetSerializer(many=True),
        operation_id="books_alias_targets",
    )
    def get(self, request):
        return Response(services.alias_targets())


class AliasBindView(APIView):
    """Append rank titles as aliases on the chosen local book (token-keyed)."""

    @extend_schema(
        request=TokenAliasBindRequestSerializer,
        responses=AliasBindResultSerializer,
        operation_id="books_alias_bind",
    )
    def post(self, request):
        body = TokenAliasBindRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        return Response(services.alias_bind(data["token"], data["aliases"]))


def cover(request, image_path):
    """Stream a local book cover."""
    return serve_media_image(conf.BOOK_ROOT, image_path, "cover")
