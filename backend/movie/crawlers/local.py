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
# 也接受 xxx (YYYY) - 720p.nfo / xxx (YYYY) [1080p].nfo 等带版本后缀的变体
# tinyMediaManager 默认命名：movie.nfo
_MP_MOVIE_NFO_RE = re.compile(r".*\(\d{4}\).*\.nfo$")


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
    # MoviePilot 有的版本只写顶层 <rating>，没有 tmm 那套 <ratings><rating name="themoviedb">...
    # 评分回退到顶层 <rating>；votes 缺失时记 0，避免整份 NFO 因投票数缺失被跳过。
    tmm_rating = root_element.find("./ratings/rating[@name='themoviedb']/value")
    tmdb_score = float(
        tmm_rating.text
        if tmm_rating is not None
        else root_element.find("rating").text
    )
    tmm_votes = root_element.find("./ratings/rating[@name='themoviedb']/votes")
    flat_votes = root_element.find("votes")
    if tmm_votes is not None:
        tmdb_votes = int(tmm_votes.text)
    elif flat_votes is not None:
        tmdb_votes = int(flat_votes.text)
    else:
        tmdb_votes = 0
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

    # 可选的中文别名补充：TMDB 没收录中文翻译的片（日剧/韩剧/小众片）
    # 在媒体目录手动建 alias.txt，每行一个别名，让榜单文本匹配能命中。
    alias = []
    if os.path.exists(os.path.join(root, "alias.txt")):
        with open(os.path.join(root, "alias.txt"), "r") as f:
            alias = f.read().splitlines()

    return LocalMovie(
        title,
        original_title,
        year,
        country_list,
        poster,
        Rate(tmdb_score, tmdb_votes, "TMDB"),
        tmdb_id,
        MovieSet(tmdb_set_id, tmdb_set_name, "TMDB"),
        alias=alias,
    )


def crawl_local(root: str) -> list:
    return scanning.scan_files(root, file_filter, process_file)
