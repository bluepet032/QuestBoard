import io
import urllib.error
from email.message import Message

import pytest

from pipeline import http
from pipeline.http import FetchError, HttpClient, RobotsDisallowed


class FakeResponse:
    def __init__(self, url: str, body: str, status: int = 200):
        self.url, self.status, self._body = url, status, body.encode("utf-8")
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"

    def read(self):
        return self._body

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def http_error(url: str, code: int, retry_after: str | None = None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(url, code, "error", headers, io.BytesIO(b""))


@pytest.fixture
def server(monkeypatch):
    """Route urlopen to a dict of url -> body or exception, and record sleeps."""

    http.reset_host_state()
    routes: dict[str, object] = {}
    calls: list[str] = []
    sleeps: list[float] = []

    def urlopen(request, timeout=None):
        url = request.full_url
        calls.append(url)
        result = routes.get(url)
        if isinstance(result, list):
            result = result.pop(0)
        if isinstance(result, Exception):
            raise result
        if result is None:
            raise http_error(url, 404)
        return FakeResponse(url, result)

    monkeypatch.setattr(http.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(http.time, "sleep", sleeps.append)
    yield routes, calls, sleeps
    http.reset_host_state()


def test_robots_disallow_blocks_the_request(server):
    routes, calls, _ = server
    routes["https://site.example/robots.txt"] = "User-agent: *\nDisallow: /private\n"

    with pytest.raises(RobotsDisallowed):
        HttpClient().get("https://site.example/private/list")

    assert "https://site.example/private/list" not in calls


def test_missing_robots_allows_and_is_fetched_once_per_host(server):
    routes, calls, _ = server
    routes["https://site.example/a"] = "a"
    routes["https://site.example/b"] = "b"

    client = HttpClient()
    assert client.get("https://site.example/a").text == "a"
    assert HttpClient().get("https://site.example/b").text == "b"

    assert calls.count("https://site.example/robots.txt") == 1


def test_unreachable_robots_is_treated_as_full_disallow(server):
    routes, _, _ = server
    routes["https://site.example/robots.txt"] = http_error("https://site.example/robots.txt", 503)

    with pytest.raises(RobotsDisallowed):
        HttpClient().get("https://site.example/list")


def test_requests_to_one_host_are_spaced_by_crawl_delay(server):
    routes, _, sleeps = server
    routes["https://site.example/robots.txt"] = "User-agent: *\nCrawl-delay: 5\n"
    routes["https://site.example/a"] = "a"
    routes["https://site.example/b"] = "b"

    client = HttpClient()
    client.get("https://site.example/a")
    client.get("https://site.example/b")

    assert sleeps and sleeps[-1] > 4


def test_retry_after_is_honoured_and_long_pauses_stop_retrying(server):
    routes, calls, sleeps = server
    url = "https://site.example/list"
    routes[url] = [http_error(url, 429, "7"), "ok"]

    assert HttpClient(min_interval=0).get(url).text == "ok"
    assert 7 in sleeps

    other = "https://site.example/slow"
    routes[other] = [http_error(other, 429, "3600"), "never"]
    with pytest.raises(FetchError):
        HttpClient(min_interval=0).get(other)
    assert calls.count(other) == 1
