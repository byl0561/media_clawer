import difflib
import re

from music.models.music import *


def album_similarity(ab1: Album, ab2: Album) -> bool:
    ab1_names = ab1.get_titles()
    ab1_year = ab1.get_year()

    ab2_names = ab2.get_titles()
    ab2_year = ab2.get_year()

    if abs(ab1_year - ab2_year) > 3:
        return False


    for ab1_name in ab1_names:
        for ab2_name in ab2_names:
            ab1_name = re.sub(r'\([^)]*\)', '', ab1_name)
            ab1_name = ab1_name.replace('/', '')
            ab1_name = ab1_name.replace(' ', '')
            ab2_name = re.sub(r'\([^)]*\)', '', ab2_name)
            ab2_name = ab2_name.replace('/', '')
            ab2_name = ab2_name.replace(' ', '')
            if difflib.SequenceMatcher(None, ab1_name, ab2_name).ratio() > 0.8:
                return True

    return False


def get_missing_albums(target_albums: list[Album], compare_albums: list[Album]) -> list[Album]:
    missing_albums = []

    for target_album in target_albums:
        found = False
        for compare_album in compare_albums:
            if album_similarity(target_album, compare_album):
                found = True
                break
        if not found:
            missing_albums.append(target_album)

    return missing_albums