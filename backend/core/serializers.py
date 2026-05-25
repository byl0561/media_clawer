"""DRF serializer base for "rated media" objects.

The domain model objects (DoubanMovie, LocalTvShow, TmdbMovie, ...) all expose
the same getter protocol, so one base serializer covers the shared fields and
each app only declares its extra keys. Return type hints are present so
drf-spectacular emits an accurate (warning-free) OpenAPI schema.
"""
from typing import Optional

from rest_framework import serializers

__all__ = [
    "RatedMediaSerializer",
    "AliasTargetSerializer",
    "AliasBindRequestSerializer",
    "AliasBindResultSerializer",
]


class RatedMediaSerializer(serializers.Serializer):
    """Serialises ``title``/``score``/``votes``/``poster``/``link``.

    ``title`` falls back to ``""`` when an object has no titles (the old code
    raised ``IndexError`` -> HTTP 500 here).
    """

    title = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    poster = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    def get_title(self, obj) -> str:
        titles = obj.get_titles()
        return titles[0] if titles else ""

    def get_score(self, obj) -> Optional[float]:
        rate = obj.get_rate()
        return round(rate.score, 1) if rate is not None else None

    def get_votes(self, obj) -> Optional[int]:
        rate = obj.get_rate()
        return rate.votes if rate is not None else None

    def get_poster(self, obj) -> Optional[str]:
        return obj.get_poster()

    def get_link(self, obj) -> Optional[str]:
        return obj.get_link()


# --- Bind alias dialog (shared by movie + tvshow apps) -----------------
# The "最新" tab gets a "绑定" button on every poster. Clicking it lists
# local items the user may bind the missing rank entry to; submitting
# appends the rank title as an alias on the chosen local folder.


class AliasTargetSerializer(serializers.Serializer):
    """One row of ``GET /api/v1/{tv-shows,anime,movies}/alias-targets``."""

    tmdb_id = serializers.IntegerField()
    title = serializers.CharField()
    year = serializers.IntegerField()
    poster = serializers.CharField(allow_null=True, required=False)


class AliasBindRequestSerializer(serializers.Serializer):
    """`POST /api/v1/{tv-shows,anime,movies}/alias-bind` request body."""

    tmdb_id = serializers.IntegerField()
    aliases = serializers.ListField(
        child=serializers.CharField(allow_blank=False), min_length=1
    )


class AliasBindResultSerializer(serializers.Serializer):
    bound = serializers.BooleanField()
    added = serializers.IntegerField()
