"""Shared (app-agnostic) HTTP endpoints."""
from django.http import Http404

from core.images import proxy_remote_image


def image_proxy(request):
    """Stream a remote poster/cover so the browser never hotlinks Douban.

    ``GET /api/v1/images/proxy?url=<absolute image url>``. Replaces the old
    client-side ``images.weserv.nl`` redirect.
    """
    url = request.GET.get("url")
    if not url:
        raise Http404()
    return proxy_remote_image(url)
