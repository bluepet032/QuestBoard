from __future__ import annotations

import html
import re
import time
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit

from pipeline.collectors.base import CollectorStructureError
from pipeline.collectors.html import StructuredHtmlCollector, clean_text, dates_from_text
from pipeline.models import RawOpportunity


ROW_RE = re.compile(r"<tr\b[^>]*>(?P<body>.*?)</tr>", re.I | re.S)
LINK_RE = re.compile(r'<a\s+href=["\'](?P<href>[^"\']*view\.do\?pbancSrnm=(?P<id>\d+)[^"\']*)["\'][^>]*>(?P<title>.*?)</a>', re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def _page_url(url: str, page: int) -> str:
    parts = urlsplit(url)
    query = {key: values[-1] for key, values in parse_qs(parts.query).items()}
    query["pageIndex"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


class GconCollector(StructuredHtmlCollector):
    def collect(self, now: datetime, limit: int = 30) -> list[RawOpportunity]:
        results: list[RawOpportunity] = []
        seen: set[str] = set()
        for page in range(1, max(2, (limit + 14) // 15 + 1)):
            response = self.client.get(_page_url(self.config.list_url, page))
            candidates: list[tuple[str, str, str]] = []
            for row in ROW_RE.finditer(response.text):
                link = LINK_RE.search(row.group("body"))
                state = clean_text(TAG_RE.sub(" ", html.unescape(row.group("body"))))
                if not link or "접수중" not in state or link.group("id") in seen:
                    continue
                seen.add(link.group("id"))
                title = clean_text(html.unescape(TAG_RE.sub(" ", link.group("title"))))
                candidates.append((urljoin(response.url, html.unescape(link.group("href"))), title, link.group("id")))
            if not candidates:
                break
            for url, title, post_id in candidates:
                detail = self.client.get(url)
                item = self._detail_item(detail.text, detail.url, title, now)
                period = re.search(r"(?:접수|신청)기간\s*[:：]?\s*(.{0,160})", item.body_text, re.I)
                if period:
                    start, end = dates_from_text(period.group(0))
                    if end and (not start or start <= end):
                        item.recruit_start, item.recruit_end, item.date_kind = start, end, "exact"
                item.source_post_id = post_id
                item.original_category = "게임/소프트웨어 · 디지털 콘텐츠"
                item.body_text = f"{title} {item.summary} 게임/소프트웨어 디지털 콘텐츠"
                results.append(item)
                if len(results) >= limit:
                    return results
                time.sleep(0.1)
        if not results:
            raise CollectorStructureError("경기콘텐츠진흥원 접수중 사업공고를 찾지 못했습니다")
        return results
