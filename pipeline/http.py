from __future__ import annotations

import gzip
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


USER_AGENT = "QuestBoard/1.0 (+https://github.com/; public-opportunity-index)"


class FetchError(RuntimeError):
    pass


@dataclass(slots=True)
class Response:
    url: str
    status: int
    text: str
    content_type: str


class HttpClient:
    def __init__(self, timeout: float = 20.0, retries: int = 3, delay: float = 0.4):
        self.timeout = timeout
        self.retries = retries
        self.delay = delay

    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        return self._request(url, headers=headers)

    def post_json(self, url: str, payload: dict, headers: dict[str, str] | None = None) -> Response:
        request_headers = {"Content-Type": "application/json; charset=utf-8"}
        if headers:
            request_headers.update(headers)
        return self._request(url, headers=request_headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _request(self, url: str, headers: dict[str, str] | None = None, data: bytes | None = None) -> Response:
        request_headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip",
        }
        if headers:
            request_headers.update(headers)

        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                request = urllib.request.Request(url, headers=request_headers, data=data)
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
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
                last_error = error
                retryable = not isinstance(error, urllib.error.HTTPError) or error.code >= 500 or error.code == 429
                if not retryable:
                    break
                if attempt + 1 < self.retries:
                    time.sleep(self.delay * (2**attempt))
        raise FetchError(f"요청 실패 ({url}): {last_error}")
