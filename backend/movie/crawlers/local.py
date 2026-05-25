"""Local movie library scanner (tinyMediaManager / MoviePilot NFO files).

Parsing rules unchanged; only the I/O plumbing (process pool, config) is now
shared via :mod:`core`.
"""
import glob
import os
import re
import xml.etree.ElementTree as ET

from core import conf, scanning
from movie.models import LocalMovie, MovieSet, Rate

# MoviePilot 默认命名：xxx (YYYY).nfo（位于 xxx (YYYY)/ 目录下）
# tinyMediaManager 默认命名：movie.nfo
_MP_MOVIE_NFO_RE = re.compile(r".*\(\d{4}\)\.nfo$")


def file_filter(file: str) -> bool:
    return file == "movie.nfo" or _MP_MOVIE_NFO_RE.match(file) is not None


def process_file(path: str):
    root, file = os.path.split(path)
    if not file_filter(file):
        return None

    # 去重：tmm + MP 混合库时，同目录可能既有 movie.nfo 又有 xxx (年).nfo。
    # MP 优先 —— 当 movie.nfo 旁边存在 MP 风格 nfo 时，跳过 movie.nfo。
    if file == "movie.nfo" and any(
        _MP_MOVIE_NFO_RE.match(f) for f in os.listdir(root)
    ):
        return None

    tree = ET.parse(os.path.join(root, file))
    root_element = tree.getroot()
    title = root_element.find("title").text
    original_title = (
        root_element.find("originaltitle").text
        if root_element.find("originaltitle") is not None
        else title
    )
    year = int(root_element.find("year").text)
    country_list = [country.text for country in root_element.findall("country")]
    tmdb_score = float(
        root_element.find("./ratings/rating[@name='themoviedb']/value").text
    )
    tmdb_votes = int(
        root_element.find("./ratings/rating[@name='themoviedb']/votes").text
    )
    tmdb_id = int(root_element.find("./uniqueid[@type='tmdb']").text)
    tmdb_set_id = (
        int(root_element.find("./uniqueid[@type='tmdbSet']").text)
        if root_element.find("./uniqueid[@type='tmdbSet']") is not None
        else None
    )
    tmdb_set_name = (
        root_element.find("./set/name").text
        if root_element.find("./set/name") is not None
        else (
            root_element.find("set").text
            if root_element.find("set") is not None
            else None
        )
    )

    poster = None
    cover_files = glob.glob(os.path.join(glob.escape(root), "poster.*"))
    if len(cover_files) > 0:
        poster = cover_files[0].replace(conf.MOVIE_ROOT, "")
        poster = f"/v1/movies/poster/{poster}"

    return LocalMovie(
        title,
        original_title,
        year,
        country_list,
        poster,
        Rate(tmdb_score, tmdb_votes, "TMDB"),
        tmdb_id,
        MovieSet(tmdb_set_id, tmdb_set_name, "TMDB"),
    )


def crawl_local(root: str) -> list:
    return scanning.scan_files(root, file_filter, process_file)
