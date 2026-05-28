"""DRF serializers for the movie endpoints (also drive the OpenAPI schema)."""
from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class MovieSerializer(RatedMediaSerializer):
    year = serializers.SerializerMethodField()

    def get_year(self, obj) -> int:
        return obj.get_year()


class MovieDiffSerializer(serializers.Serializer):
    """`GET /api/v1/movies/diff` response."""

    missing = MovieSerializer(many=True)
    extra = MovieSerializer(many=True)


class MovieSeriesGapSerializer(serializers.Serializer):
    """One element of `GET /api/v1/movies/series-gaps` (a list).

    Each row carries the full picture of one owned TMDB collection: id, name,
    a vote-weighted score across the whole collection, the local entries the
    user already owns, and the entries still missing.
    """

    collection_id = serializers.IntegerField()
    collection_name = serializers.CharField(allow_null=True)
    score = serializers.FloatField(allow_null=True)
    votes = serializers.IntegerField()
    local = MovieSerializer(many=True)
    missing = MovieSerializer(many=True)


class IgnoreCollectionRequestSerializer(serializers.Serializer):
    """`POST /api/v1/movies/ignore-collection` request body."""

    collection_id = serializers.IntegerField()


class IgnoreCollectionResultSerializer(serializers.Serializer):
    """How many local movies actually had the id newly written."""

    updated = serializers.IntegerField()
