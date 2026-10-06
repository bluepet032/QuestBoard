from __future__ import annotations

import gzip
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser


ROBOTS_AGENT = "QuestBoard"
USER_AGENT = f"{ROBOTS_AGENT}/1.0 (+https://github.com/bluepet032/QuestBoard; public-opportunity-index)"
MIN_HOST_INTERVAL = 1.0
MAX_RETRY_AFTER = 30.0


class FetchError(RuntimeError):
    pass


class RobotsDisallowed(FetchError):
    pass


@dataclass(slots=True)
class Response:
    url: str
    status: int
    text: str
    content_type: str


# Shared across collectors in one pipeline run: robots.txt is read once per host and
# requests to the same host are spaced out even when several collectors use it.
_robots: dict[str, RobotFileParser] = {}
_last_request: dict[str, float] = {}


def reset_host_state() -> None:
    _robots.clear()
    _last_request.clear()


def retry_after_seconds(value: str | None) -> float | None:
    try:
        return max(0.0, float(value)) if value else None
    except ValueError:
        return None


class HttpClient:
    def __init__(self, timeout: float = 20.0, retries: int = 3, delay: float = 0.4,
                 min_interval: float = MIN_HOST_INTERVAL, respect_robots: bool = True):
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.min_interval = min_interval
        self.respect_robots = respect_robots

    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        return self._request(url, headers=headers)

    def post_json(self, url: str, payload: dict, headers: dict[str, str] | None = None) -> Response:
        request_headers = {"Content-Type": "application/json; charset=utf-8"}
        if headers:
            request_headers.update(headers)
        return self._request(url, headers=request_headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _robots_for(self, url: str) -> RobotFileParser:
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host in _robots:
            return _robots[host]
        parser = RobotFileParser()
        try:
            response = self._send(f"{host}/robots.txt", {"User-Agent": USER_AGENT})
            parser.parse(response.text.splitlines())
        except urllib.error.HTTPError as error:
            # RFC 9309: a 4xx robots.txt means no restrictions; 5xx means assume full disallow.
            if error.code >= 500:
                parser.disallow_all = True
            else:
                parser.allow_all = True
        except (urllib.error.URLError, TimeoutError):
            parser.disallow_all = True
        _robots[host] = parser
        return parser

    def _wait_for_host(self, url: str, crawl_delay: float) -> None:
        host = urlsplit(url).netloc
        interval = max(self.min_interval, crawl_delay)
        elapsed = time.monotonic() - _last_request.get(host, float("-inf"))
        if elapsed < interval:
            time.sleep(interval - elapsed)
        _last_request[host] = time.monotonic()

    def _send(self, url: str, headers: dict[str, str], data: bytes | None = None) -> Response:
        request = urllib.request.Request(url, headers=headers, data=data)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = response.read()
            if response.headers.get("Content-Encoding") == "gzip":
                payload = gzip.decompress(payload)
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                text = payload.decode(charset, errors="replace")
            except LookupError:
                text = payload.decode("utf-8", errors="replace")
            return Response(
                url=response.geturl(),
                status=response.status,
                text=text,
                content_type=response.headers.get_content_type(),
            )

    def _request(self, url: str, headers: dict[str, str] | None = None, data: bytes | None = None) -> Response:
        request_headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip",
        }
        if headers:
            request_headers.update(headers)

        crawl_delay = 0.0
        if self.respect_robots:
            robots = self._robots_for(url)
            if not robots.can_fetch(ROBOTS_AGENT, url):
                raise RobotsDisallowed(f"robots.txt가 수집을 허용하지 않습니다 ({url})")
            crawl_delay = float(robots.crawl_delay(ROBOTS_AGENT) or 0)

        last_error: Exception | None = None
        for attempt in range(self.retries):
            self._wait_for_host(url, crawl_delay)
            try:
                return self._send(url, request_headers, data)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
                last_error = error
                is_http = isinstance(error, urllib.error.HTTPError)
                retryable = not is_http or error.code >= 500 or error.code == 429
                if not retryable or attempt + 1 >= self.retries:
                    break
                wait = self.delay * (2**attempt)
                if is_http and error.code in {429, 503}:
                    requested = retry_after_seconds(error.headers.get("Retry-After"))
                    if requested is not None and requested > MAX_RETRY_AFTER:
                        # The server asked for a long pause; stop instead of hammering it.
                        break
                    wait = max(wait, requested or 0)
                time.sleep(wait)
        raise FetchError(f"요청 실패 ({url}): {last_error}")
