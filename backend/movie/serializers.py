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


class MovieCollectionGapSerializer(serializers.Serializer):
    """One element of `GET /api/v1/movies/collection-gaps` (a list)."""

    collection = serializers.CharField()
    missing = MovieSerializer(many=True)
