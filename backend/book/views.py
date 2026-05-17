"""Book HTTP endpoints (thin: work lives in :mod:`book.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from book import services
from book.serializers import BookDiffSerializer


class DiffView(APIView):
    """Douban Top 250 books vs. the local book library."""

    @extend_schema(responses=BookDiffSerializer, operation_id="books_diff")
    def get(self, request):
        return Response(services.diff())


def cover(request, image_path):
    """Stream a local book cover."""
    return serve_media_image(conf.BOOK_ROOT, image_path, "cover")
