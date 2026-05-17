"""Local album scanner ("{title} - {artist} {year}" folders). Rules unchanged."""
import glob
import os
import re

from core import conf, scanning
from music.models import LocalAlbum

_DIR_PATTERN = re.compile(r"^(.+)\s-\s(.+)\s(\d{4})$")


def dir_filter(d: str) -> bool:
    return _DIR_PATTERN.match(d) is not None


def process_dir(path: str):
    root, d = os.path.split(path)

    match = _DIR_PATTERN.match(d)
    if not match:
        return None

    title = match.group(1)
    artist = match.group(2)
    year = int(match.group(3))

    alias = []
    if os.path.exists(os.path.join(root, d, "alias.txt")):
        with open(os.path.join(root, d, "alias.txt"), "r") as f:
            alias = f.readlines()

    poster = None
    cover_files = glob.glob(os.path.join(glob.escape(path), "cover.*"))
    if len(cover_files) > 0:
        poster = "/album/cover/" + cover_files[0].replace(conf.MUSIC_ROOT, "")

    return LocalAlbum(title, alias, artist, year, poster)


def crawl_local(root: str) -> list:
    return scanning.scan_dirs(root, dir_filter, process_dir)
