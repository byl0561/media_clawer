import mimetypes

from django.http import JsonResponse, Http404, HttpResponse

from music.utils.local_music import *
from music.utils.douban_music import *
from music.utils.common import *
from utils.file_utils import read_image_file


def diff_douban_250(request):
    douban_250_albums = crawl_douban_250()
    local_albums = crawl_local(music_folder)
    missing_albums = get_missing_albums(douban_250_albums, local_albums)
    extra_albums = get_missing_albums(local_albums, douban_250_albums)

    return JsonResponse({
        'missing_albums': [missing_album.to_dict() for missing_album in missing_albums],
        'extra_albums': [extra_album.to_dict() for extra_album in extra_albums],
    })


def get_cover(request, image_path):
    full_path = os.path.join(music_folder, image_path)
    if not os.path.splitext(full_path)[0].endswith('cover'):
        raise Http404()

    data = read_image_file(full_path)
    if data is None:
        raise Http404()

    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    return HttpResponse(data, content_type=mime_type)
