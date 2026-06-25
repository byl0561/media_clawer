"""Shared API exceptions (plain Python; HTTP status set by FastAPI handlers)."""


class UpstreamUnavailable(Exception):
    status_code = 503
    detail = "上游榜单数据暂不可用，请稍后重试。"
    code = "upstream_unavailable"


class ShowNotFound(Exception):
    status_code = 404
    detail = "未在本地库中找到对应条目（nfo 的 tmdb id 不匹配）。"
    code = "show_not_found"
