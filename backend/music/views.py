"""Album HTTP endpoints (thin: work lives in :mod:`music.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from music import services
from music.serializers import AlbumDiffSerializer


class DiffView(APIView):
    """Douban Top 250 albums vs. the local album library."""

    @extend_schema(responses=AlbumDiffSerializer, operation_id="albums_diff")
    def get(self, request):
        return Response(services.diff())


def cover(request, image_path):
    """Stream a local album cover."""
    return serve_media_image(conf.MUSIC_ROOT, image_path, "cover")
