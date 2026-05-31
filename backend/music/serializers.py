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


class AlbumLyricGapSerializer(serializers.Serializer):
    """One row of `GET /api/v1/albums/lyric-gaps` — token-keyed for ignore."""

    token = serializers.CharField()
    title = serializers.CharField()
    artist = serializers.CharField(allow_null=True, required=False)
    year = serializers.IntegerField(required=False)
    poster = serializers.CharField(allow_null=True, required=False)


class IgnoreLyricRequestSerializer(serializers.Serializer):
    """`POST /api/v1/albums/ignore-lyric` request body."""

    token = serializers.CharField()


class IgnoreLyricResultSerializer(serializers.Serializer):
    """True iff the flag was newly written (idempotent re-clicks return False)."""

    updated = serializers.BooleanField()
