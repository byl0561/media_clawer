"""DRF serializer base for "rated media" objects.

The domain model objects (DoubanMovie, LocalTvShow, TmdbMovie, ...) all expose
the same getter protocol, so one base serializer covers the shared fields and
each app only declares its extra keys. Output is byte-compatible with the old
hand-written ``to_dict()`` payloads the Vue frontend already consumes.
"""
from rest_framework import serializers

__all__ = ["RatedMediaSerializer"]


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

    def get_score(self, obj):
        rate = obj.get_rate()
        return rate.score if rate is not None else None

    def get_votes(self, obj):
        rate = obj.get_rate()
        return rate.votes if rate is not None else None

    def get_poster(self, obj):
        return obj.get_poster()

    def get_link(self, obj):
        return obj.get_link()
