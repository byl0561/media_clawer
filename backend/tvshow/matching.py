"""TV/anime similarity rules (logic identical to the original ``utils.common``)."""
from core.matching import find_missing, strip_parentheses, title_ratio
from tvshow.models import TvShow


def gap_year(interval1, interval2) -> int:
    start1, end1 = interval1
    start2, end2 = interval2
    return max(0, max(start1, start2) - min(end1, end2))


def tv_show_similarity(show1: TvShow, show2: TvShow) -> bool:
    if gap_year(show1.get_years(), show2.get_years()) > 3:
        return False
    for name1 in show1.get_titles():
        for name2 in show2.get_titles():
            if (
                title_ratio(
                    strip_parentheses(name1, ascii_only=True),
                    strip_parentheses(name2, ascii_only=True),
                )
                > 0.8
            ):
                return True
    return False


def combine_tv_show(tv_shows1: list, tv_shows2: list) -> list:
    combined = list(tv_shows1)
    for tv_show2 in tv_shows2:
        if not any(tv_show_similarity(tv_show2, c) for c in combined):
            combined.append(tv_show2)
    return combined


def get_missing_tv_shows(target_tv_shows: list, compare_tv_shows: list) -> list:
    return find_missing(target_tv_shows, compare_tv_shows, tv_show_similarity)
