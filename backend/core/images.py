"""Safe poster / cover serving.

The original per-app views did ``os.path.join(folder, user_supplied_path)``
guarded only by an ``endswith('poster')`` check, so a request such as
``../../../etc/secret-poster.png`` escaped the media library. Here the
resolved path is required to stay inside the library root, and the file is
streamed with :class:`~django.http.FileResponse` instead of being slurped
into memory.
"""
import mimetypes
import os

from django.http import FileResponse, Http404

__all__ = ["serve_media_image"]

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}


def serve_media_image(media_root: str, rel_path: str, stem_suffix: str) -> FileResponse:
    """Stream ``<media_root>/<rel_path>`` if it is a legitimate image.

    Raises :class:`~django.http.Http404` unless the resolved path stays within
    ``media_root``, its filename stem ends with ``stem_suffix`` ("poster" /
    "cover") and it has an allowed image extension.
    """
    base = os.path.realpath(media_root)
    target = os.path.realpath(os.path.join(media_root, rel_path))

    if target != base and not target.startswith(base + os.sep):
        raise Http404()

    stem, ext = os.path.splitext(target)
    if not stem.endswith(stem_suffix):
        raise Http404()
    if ext.lower() not in _ALLOWED_EXTENSIONS:
        raise Http404()
    if not os.path.isfile(target):
        raise Http404()

    content_type, _ = mimetypes.guess_type(target)
    return FileResponse(
        open(target, "rb"),
        content_type=content_type or "application/octet-stream",
    )
