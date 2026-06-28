import cloudscraper
from constants import HEADERS

_client = None
DEFAULT_TIMEOUT_SECONDS = 60


def get_http_client():
    global _client
    if _client is not None:
        return _client

    try:
        from curl_cffi import requests as curl_requests

        _client = curl_requests.Session(impersonate="chrome146")
    except ImportError:
        _client = cloudscraper.create_scraper()

    _client.headers.update(HEADERS)
    return _client


def http_get(url: str, *, headers: dict | None = None, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    client = get_http_client()
    if headers:
        return client.get(url, headers=headers, timeout=timeout)
    return client.get(url, timeout=timeout)
