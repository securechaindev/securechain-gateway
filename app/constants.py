from enum import Enum

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class RateLimit(str, Enum):
    HEALTH_CHECK = "25/minute"
    PROXY_AUTH = "75/minute"
    PROXY_DEPEX = "75/minute"
    PROXY_VEXGEN = "75/minute"
