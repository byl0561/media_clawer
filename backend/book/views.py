"""Book HTTP endpoints (thin: work lives in :mod:`book.services`)."""
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from book import services


class DoubanDiffView(APIView):
    """``GET book/douban250/diff``."""

    def get(self, request):
        return Response(services.douban250_diff())


def cover(request, image_path):
    """``GET book/cover/<path>`` — stream a local book cover."""
    return serve_media_image(conf.BOOK_ROOT, image_path, "cover")
