from tvshow.models.tvshow import *
import difflib
import re


def gap_year(interval1, interval2) -> int:
    start1, end1 = interval1
    start2, end2 = interval2
    return max(0, max(start1, start2) - min(end1, end2))


def tv_show_similarity(show1: TvShow, show2: TvShow) -> bool:
    show1_names = show1.get_titles()
    show1_years = show1.get_years()

    show2_names = show2.get_titles()
    show2_years = show2.get_years()

    if gap_year(show1_years, show2_years) > 3:
        return False

    for show1_name in show1_names:
        for show2_name in show2_names:
            show1_name = re.sub(r'\([^)]*\)', '', show1_name)
            show2_name = re.sub(r'\([^)]*\)', '', show2_name)
            if difflib.SequenceMatcher(None, show1_name, show2_name).ratio() > 0.8:
                return True

    return False


def combine_tv_show(tv_shows1: list[TvShow], tv_shows2: list[TvShow]) -> list[TvShow]:
    combined_tv_shows = []
    combined_tv_shows.extend(tv_shows1)

    for tv_show2 in tv_shows2:
        found = False
        for combined_tv_show in combined_tv_shows:
            if tv_show_similarity(tv_show2, combined_tv_show):
                found = True
                break
        if not found:
            combined_tv_shows.append(tv_show2)

    return combined_tv_shows


def get_missing_tv_shows(target_tv_shows: list[TvShow], compare_tv_shows: list[TvShow]) -> list[TvShow]:
    missing_tv_shows = []

    for target_tv_show in target_tv_shows:
        found = False
        for compare_tv_show in compare_tv_shows:
            if tv_show_similarity(target_tv_show, compare_tv_show):
                found = True
                break
        if not found:
            missing_tv_shows.append(target_tv_show)

    return missing_tv_shows
