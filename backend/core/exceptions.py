"""Shared API exceptions."""
from rest_framework.exceptions import APIException


class UpstreamUnavailable(APIException):
    """Raised when a ranking source crawl returns nothing.

    The Top250 / doulist / Bangumi pages always contain items, so an empty
    result means the fetch failed. Returning a 503 instead of an empty diff
    avoids the misleading "your whole local library is outdated" payload
    (every local item would otherwise be reported as ``extra``).
    """

    status_code = 503
    default_detail = "上游榜单数据暂不可用，请稍后重试。"
    default_code = "upstream_unavailable"


class ShowNotFound(APIException):
    """No local nfo has a tmdb ``uniqueid`` matching the request.

    The ignore / bind-alias endpoints locate the item on disk by its TMDB id;
    a mismatch means the library moved/renamed or the id is stale, which is a
    404 rather than a server error. Used by both tv and movie endpoints.
    """

    status_code = 404
    default_detail = "未在本地库中找到对应条目（nfo 的 tmdb id 不匹配）。"
    default_code = "show_not_found"
