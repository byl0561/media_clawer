import os
import re

from music.models.music import LocalAlbum


def crawl_local(music_folder: str) -> list[LocalAlbum]:
    albums = []

    pattern = r'^(.+)\s-\s(.+)\s(\d{4})$'
    for root, dirs, files in os.walk(music_folder):
        for d in dirs:
            match = re.match(pattern, d)
            if not match:
                continue

            title = match.group(1)
            artist = match.group(2)
            year = int(match.group(3))

            alias = []
            if os.path.exists(os.path.join(root, d, 'alias.txt')):
                with open(os.path.join(root, d, 'alias.txt'), 'r') as f:
                    alias = f.readlines()
            albums.append(LocalAlbum(title, alias, artist, year))
    return albums
