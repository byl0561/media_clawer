"""TV/anime HTTP endpoints (thin: work lives in :mod:`tvshow.services`)."""
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core import conf
from core.images import serve_media_image
from core.serializers import (
    AliasBindRequestSerializer,
    AliasBindResultSerializer,
    AliasTargetSerializer,
)
from tvshow import services
from tvshow.serializers import (
    IgnoreOptionsSerializer,
    IgnoreRequestSerializer,
    IgnoreResultSerializer,
    LocalGapSerializer,
    ShowDiffSerializer,
)


class TvDiffView(APIView):
    """Douban TV doulists vs. the local TV library."""

    @extend_schema(responses=ShowDiffSerializer, operation_id="tv_shows_diff")
    def get(self, request):
        return Response(services.tv_diff())


class AnimeDiffView(APIView):
    """Bangumi TV ranking vs. the local anime library."""

    @extend_schema(responses=ShowDiffSerializer, operation_id="anime_diff")
    def get(self, request):
        return Response(services.anime_diff())


class TvLocalGapsView(APIView):
    """Local TV shows missing whole seasons and/or behind on episodes."""

    @extend_schema(
        responses=LocalGapSerializer(many=True), operation_id="tv_shows_local_gaps"
    )
    def get(self, request):
        return Response(services.local_gaps("tv"))


class AnimeLocalGapsView(APIView):
    """Local anime missing whole seasons and/or behind on episodes."""

    @extend_schema(
        responses=LocalGapSerializer(many=True), operation_id="anime_local_gaps"
    )
    def get(self, request):
        return Response(services.local_gaps("anime"))


class _IgnoreOptionsView(APIView):
    """Gap seasons + selectable episodes for the ignore dialog.

    ``GET ?tmdb_id=<int>``. TMDB is fetched here (on dialog open), not on
    every gap render. Subclasses set ``library``.
    """

    library: str = ""

    @extend_schema(responses=IgnoreOptionsSerializer)
    def get(self, request):
        raw = request.query_params.get("tmdb_id")
        try:
            tmdb_id = int(raw)
        except (TypeError, ValueError):
            raise ValidationError({"tmdb_id": "integer query param required"})
        return Response(services.ignore_options(self.library, tmdb_id))


class _IgnoreView(APIView):
    """Write the per-season skip markers chosen in the dialog.

    ``POST {tmdb_id, selections:[{season_num, episode}]}``. Subclasses set
    ``library``.
    """

    library: str = ""

    @extend_schema(
        request=IgnoreRequestSerializer, responses=IgnoreResultSerializer
    )
    def post(self, request):
        body = IgnoreRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        return Response(
            services.ignore_apply(
                self.library, data["tmdb_id"], data["selections"]
            )
        )


class TvIgnoreOptionsView(_IgnoreOptionsView):
    library = "tv"


class AnimeIgnoreOptionsView(_IgnoreOptionsView):
    library = "anime"


class TvIgnoreView(_IgnoreView):
    library = "tv"


class AnimeIgnoreView(_IgnoreView):
    library = "anime"


# --- Alias bind --------------------------------------------------------


class _AliasTargetsView(APIView):
    """All local items the user may bind a missing rank entry to.

    ``GET`` returns ``[{tmdb_id, title, year, poster}, ...]``. Subclasses set
    ``library``.
    """

    library: str = ""

    @extend_schema(responses=AliasTargetSerializer(many=True))
    def get(self, request):
        return Response(services.alias_targets(self.library))


class _AliasBindView(APIView):
    """Append rank titles as aliases on the chosen local item.

    ``POST {tmdb_id, aliases:[str]}``. Subclasses set ``library``.
    """

    library: str = ""

    @extend_schema(
        request=AliasBindRequestSerializer, responses=AliasBindResultSerializer
    )
    def post(self, request):
        body = AliasBindRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        return Response(
            services.alias_bind(self.library, data["tmdb_id"], data["aliases"])
        )


class TvAliasTargetsView(_AliasTargetsView):
    library = "tv"


class AnimeAliasTargetsView(_AliasTargetsView):
    library = "anime"


class TvAliasBindView(_AliasBindView):
    library = "tv"


class AnimeAliasBindView(_AliasBindView):
    library = "anime"


def tv_poster(request, image_path):
    return serve_media_image(conf.TV_ROOT, image_path, "poster")


def anime_poster(request, image_path):
    return serve_media_image(conf.ANIME_ROOT, image_path, "poster")
