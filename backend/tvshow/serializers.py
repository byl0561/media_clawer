"""DRF serializers for the TV/anime endpoints (also drive the OpenAPI schema).

``year`` is the ``[start, end]`` list the original payload returned (the
frontend ignores it but the shape is preserved).
"""
from typing import List, Optional

from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class TvShowSerializer(RatedMediaSerializer):
    year = serializers.SerializerMethodField()
    # Only TMDB/local shows carry a tmdb_id; Douban/Bangumi diff items don't,
    # so this is null for those. The local-gaps "show" is the TMDB object, so
    # the frontend gets the id it needs to open the ignore dialog.
    tmdb_id = serializers.SerializerMethodField()

    def get_year(self, obj) -> List[int]:
        return obj.get_years()

    def get_tmdb_id(self, obj) -> Optional[int]:
        return getattr(obj, "tmdb_id", None)


class SeasonRefSerializer(serializers.Serializer):
    """One season identifier + display fields (poster + chinese name + TMDB score)."""

    num = serializers.IntegerField()
    name = serializers.CharField()
    poster = serializers.CharField(allow_null=True, required=False)
    score = serializers.FloatField(allow_null=True, required=False)


class IncompleteSeasonSerializer(serializers.Serializer):
    season_num = serializers.IntegerField()
    season_name = serializers.CharField()
    local_max_episode = serializers.IntegerField()
    remote_max_episode = serializers.IntegerField()


class ShowDiffSerializer(serializers.Serializer):
    """`GET /api/v1/{tv-shows,anime}/diff` response."""

    missing = TvShowSerializer(many=True)
    extra = TvShowSerializer(many=True)


class SeriesGapSerializer(serializers.Serializer):
    """One element of `GET /api/v1/{tv-shows,anime}/series-gaps` (a list)."""

    show = TvShowSerializer()
    local_seasons = SeasonRefSerializer(many=True)
    missing_seasons = SeasonRefSerializer(many=True)
    incomplete_seasons = IncompleteSeasonSerializer(many=True)


class SubtitleGapSeasonSerializer(serializers.Serializer):
    """A season tile in the subtitle-gap card."""

    num = serializers.IntegerField()
    name = serializers.CharField()
    poster = serializers.CharField(allow_null=True, required=False)
    score = serializers.FloatField(allow_null=True, required=False)
    missing_count = serializers.IntegerField()
    max_missing_episode = serializers.IntegerField()


class SubtitleGapSerializer(serializers.Serializer):
    """`GET /api/v1/{tv-shows,anime}/subtitle-gaps` row."""

    show = TvShowSerializer()
    seasons = SubtitleGapSeasonSerializer(many=True)


# --- Ignore dialog -----------------------------------------------------


class IgnoreEpisodeSerializer(serializers.Serializer):
    num = serializers.IntegerField()
    name = serializers.CharField()
    date = serializers.CharField(allow_null=True)


class IgnoreSeasonSerializer(serializers.Serializer):
    season_num = serializers.IntegerField()
    season_name = serializers.CharField()
    local_max_episode = serializers.IntegerField()
    latest_episode = serializers.IntegerField()
    episodes = IgnoreEpisodeSerializer(many=True)


class IgnoreOptionsSerializer(serializers.Serializer):
    """`GET /api/v1/{tv-shows,anime}/ignore-options?tmdb_id=` response."""

    title = serializers.CharField()
    seasons = IgnoreSeasonSerializer(many=True)


class IgnoreSelectionSerializer(serializers.Serializer):
    season_num = serializers.IntegerField(min_value=0)
    episode = serializers.IntegerField(min_value=0)


class IgnoreRequestSerializer(serializers.Serializer):
    """`POST /api/v1/{tv-shows,anime}/ignore` request body."""

    tmdb_id = serializers.IntegerField()
    selections = IgnoreSelectionSerializer(many=True)


class IgnoreResultSerializer(serializers.Serializer):
    fully_ignored = serializers.BooleanField()
