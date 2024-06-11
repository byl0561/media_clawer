from django.http import JsonResponse

from constant import music_folder
from music.utils.local_music import *
from music.utils.douban_music import *
from music.utils.common import *


def diff_douban_250(request):
    douban_250_albums = crawl_douban_250()
    local_albums = crawl_local(music_folder)
    missing_albums = get_missing_albums(douban_250_albums, local_albums)
    extra_albums = get_missing_albums(local_albums, douban_250_albums)

    return JsonResponse({
        'missing_albums': [missing_album.to_dict() for missing_album in missing_albums],
        'extra_albums': [extra_album.to_dict() for extra_album in extra_albums],
    })
