"""DRF serializer producing the legacy album payload (adds ``artist``/``year``)."""
from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class AlbumSerializer(RatedMediaSerializer):
    artist = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()

    def get_artist(self, obj):
        return obj.get_artist()

    def get_year(self, obj) -> int:
        return obj.get_year()
