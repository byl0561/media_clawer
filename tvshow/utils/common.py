from tvshow.models.tvshow import *
import difflib


def is_overlapping(interval1, interval2):
    if interval1[1] < interval2[0] or interval2[1] < interval1[0]:
        return False
    return True


def tv_show_similarity(show1: TvShow, show2: TvShow) -> bool:
    show1_names = show1.get_titles()
    show1_years = show1.get_years()

    show2_names = show2.get_titles()
    show2_years = show2.get_years()

    if is_overlapping(show1_years, show2_years) > 2:
        return False

    for show1_name in show1_names:
        for show2_name in show2_names:
            if difflib.SequenceMatcher(None, show1_name, show2_name).ratio() > 0.9:
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