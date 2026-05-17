"""DRF serializer producing the legacy book payload (adds ``author``)."""
from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class BookSerializer(RatedMediaSerializer):
    author = serializers.SerializerMethodField()

    def get_author(self, obj):
        return obj.get_author()
