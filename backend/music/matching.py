"""Album similarity rules (logic identical to the original ``utils.common``)."""
from core.matching import find_missing, strip_parentheses, title_ratio
from music.models import Album


def _normalize(name: str) -> str:
    return strip_parentheses(name, ascii_only=True).replace("/", "").replace(" ", "")


def album_similarity(ab1: Album, ab2: Album) -> bool:
    if abs(ab1.get_year() - ab2.get_year()) > 3:
        return False
    for name1 in ab1.get_titles():
        for name2 in ab2.get_titles():
            if title_ratio(_normalize(name1), _normalize(name2)) > 0.8:
                return True
    return False


def get_missing_albums(target_albums: list, compare_albums: list) -> list:
    return find_missing(target_albums, compare_albums, album_similarity)
