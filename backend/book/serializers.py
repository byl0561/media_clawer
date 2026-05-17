"""DRF serializers for the book endpoints (also drive the OpenAPI schema)."""
from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class BookSerializer(RatedMediaSerializer):
    author = serializers.SerializerMethodField()

    def get_author(self, obj) -> str:
        return obj.get_author()


class BookDiffSerializer(serializers.Serializer):
    """`GET /api/v1/books/diff` response."""

    missing = BookSerializer(many=True)
    extra = BookSerializer(many=True)
