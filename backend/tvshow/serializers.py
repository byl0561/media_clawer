"""DRF serializers producing the legacy TV/anime payloads.

``year`` is intentionally the ``[start, end]`` list the old ``TvShow.to_dict``
returned (the frontend ignores it but the shape is preserved).
"""
from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class TvShowSerializer(RatedMediaSerializer):
    year = serializers.SerializerMethodField()

    def get_year(self, obj):
        return obj.get_years()


class SeasonSerializer(serializers.Serializer):
    num = serializers.IntegerField()
    name = serializers.CharField()
