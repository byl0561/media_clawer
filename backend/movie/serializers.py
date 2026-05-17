"""DRF serializer producing the legacy movie payload (adds ``year``)."""
from rest_framework import serializers

from core.serializers import RatedMediaSerializer


class MovieSerializer(RatedMediaSerializer):
    year = serializers.SerializerMethodField()

    def get_year(self, obj) -> int:
        return obj.get_year()
