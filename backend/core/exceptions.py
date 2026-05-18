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
