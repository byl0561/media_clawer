"""DRF serializers for the album endpoints (also drive the OpenAPI schema)."""
from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class AlbumSerializer(RatedMediaSerializer):
    artist = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()

    def get_artist(self, obj) -> str:
        return obj.get_artist()

    def get_year(self, obj) -> int:
        return obj.get_year()


class AlbumDiffSerializer(serializers.Serializer):
    """`GET /api/v1/albums/diff` response."""

    missing = AlbumSerializer(many=True)
    extra = AlbumSerializer(many=True)
