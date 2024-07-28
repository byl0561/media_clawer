import glob
import os
import re

from constant import music_folder
from music.models.music import LocalAlbum
from utils import file_utils


def dir_filter(d: str) -> bool:
    pattern = r'^(.+)\s-\s(.+)\s(\d{4})$'
    return re.match(pattern, d) is not None


def process_dir(path: str):
    root, d = os.path.split(path)

    pattern = r'^(.+)\s-\s(.+)\s(\d{4})$'
    match = re.match(pattern, d)
    if not match:
        return None

    title = match.group(1)
    artist = match.group(2)
    year = int(match.group(3))

    alias = []
    if os.path.exists(os.path.join(root, d, 'alias.txt')):
        with open(os.path.join(root, d, 'alias.txt'), 'r') as f:
            alias = f.readlines()

    poster = None
    pattern = os.path.join(glob.escape(path), 'cover.*')
    cover_files = glob.glob(pattern)
    if len(cover_files) > 0:
        poster = cover_files[0].replace(music_folder, '')
        poster = f'/album/cover/{poster}'
    return LocalAlbum(title, alias, artist, year, poster)


def crawl_local(music_folder: str) -> list[LocalAlbum]:
    return file_utils.mapping_dir_to_object(music_folder, dir_filter, process_dir)
