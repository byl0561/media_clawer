"""DRF serializers for the TV/anime endpoints (also drive the OpenAPI schema).

``year`` is the ``[start, end]`` list the original payload returned (the
frontend ignores it but the shape is preserved).
"""
from typing import List

from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class TvShowSerializer(RatedMediaSerializer):
    year = serializers.SerializerMethodField()

    def get_year(self, obj) -> List[int]:
        return obj.get_years()


class SeasonSerializer(serializers.Serializer):
    num = serializers.IntegerField()
    name = serializers.CharField()


class IncompleteSeasonSerializer(serializers.Serializer):
    season_num = serializers.IntegerField()
    season_name = serializers.CharField()
    local_max_episode = serializers.IntegerField()
    remote_max_episode = serializers.IntegerField()


class ShowDiffSerializer(serializers.Serializer):
    """`GET /api/v1/{tv-shows,anime}/diff` response."""

    missing = TvShowSerializer(many=True)
    extra = TvShowSerializer(many=True)


class LocalGapSerializer(serializers.Serializer):
    """One element of `GET /api/v1/{tv-shows,anime}/local-gaps` (a list)."""

    show = TvShowSerializer()
    missing_seasons = SeasonSerializer(many=True)
    incomplete_seasons = IncompleteSeasonSerializer(many=True)
