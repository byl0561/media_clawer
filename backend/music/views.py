"""Album HTTP endpoints (thin: work lives in :mod:`music.services`)."""
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from music import services


class DoubanDiffView(APIView):
    """``GET album/douban250/diff``."""

    def get(self, request):
        return Response(services.douban250_diff())


def cover(request, image_path):
    """``GET album/cover/<path>`` — stream a local album cover."""
    return serve_media_image(conf.MUSIC_ROOT, image_path, "cover")
