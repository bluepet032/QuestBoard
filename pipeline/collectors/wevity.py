from __future__ import annotations

import html
import re
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit

from pipeline.collectors.base import Collector, CollectorStructureError
from pipeline.collectors.html import clean_text
from pipeline.models import RawOpportunity


ROW_RE = re.compile(r"<li\b[^>]*>(?P<body>.*?)</li>", re.I | re.S)
LINK_RE = re.compile(
    r'<div\s+class=["\']tit["\'][^>]*>.*?<a\s+href=["\'](?P<href>[^"\']*gbn=view[^"\']*)["\'][^>]*>(?P<title>.*?)</a>',
    re.I | re.S,
)
TAG_RE = re.compile(r"<[^>]+>")
DDAY_RE = re.compile(r"D-(\d+)", re.I)


def _text(markup: str) -> str:
    return clean_text(TAG_RE.sub(" ", html.unescape(markup)))


def _div_text(markup: str, class_name: str) -> str:
    match = re.search(rf'<div\s+class=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'][^>]*>(?P<body>.*?)</div>', markup, re.I | re.S)
    return _text(match.group("body")) if match else ""


def _with_query(url: str, **updates: str | int) -> str:
    parts = urlsplit(url)
    query = {key: values[-1] for key, values in parse_qs(parts.query).items()}
    query.update({key: str(value) for key, value in updates.items()})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


class WevityCollector(Collector):
    """Collect Wevity's IT and game categories instead of sampling its front page."""

    CATEGORY_IDS = ("21", "20")  # 게임/소프트웨어, 웹/모바일/IT
    MODES = ("soon", "ing", "future")

    def collect(self, now: datetime, limit: int = 30) -> list[RawOpportunity]:
        results: list[RawOpportunity] = []
        seen: set[str] = set()
        exhausted: set[tuple[str, str]] = set()
        max_pages = max(2, (limit + 19) // 20 + 1)

        for page in range(1, max_pages + 1):
            for category_id in self.CATEGORY_IDS:
                for mode in self.MODES:
                    key = (category_id, mode)
                    if key in exhausted:
                        continue
                    url = _with_query(self.config.list_url, cidx=category_id, gbn="list", mode=mode, gp=page)
                    response = self.client.get(url)
                    page_items = self._parse_page(response.text, response.url, now)
                    new_items = [item for item in page_items if item.source_post_id not in seen]
                    if not page_items:
                        exhausted.add(key)
                        continue
                    for item in new_items:
                        seen.add(item.source_post_id or item.source_url)
                        results.append(item)
                    if len(results) >= limit:
                        return results[:limit]
            if len(exhausted) == len(self.CATEGORY_IDS) * len(self.MODES):
                break

        if not results:
            raise CollectorStructureError("위비티 IT·게임 분류에서 공모전 항목을 찾지 못했습니다")
        return results[:limit]

    def _parse_page(self, markup: str, base_url: str, now: datetime) -> list[RawOpportunity]:
        results: list[RawOpportunity] = []
        for match in ROW_RE.finditer(markup):
            body = match.group("body")
            link = LINK_RE.search(body)
            if not link or "sub-tit" not in body or "organ" not in body:
                continue
            fields = {name: _div_text(body, name) for name in ("sub-tit", "organ", "day")}
            title = _text(link.group("title"))
            href = html.unescape(link.group("href"))
            source_url = urljoin(base_url, href)
            query = parse_qs(urlsplit(source_url).query)
            post_id = (query.get("ix") or [source_url])[0]
            category = re.sub(r"^분야\s*:\s*", "", fields.get("sub-tit", ""))
            dday = DDAY_RE.search(fields.get("day", ""))
            recruit_end = (now.date() + timedelta(days=int(dday.group(1)))).isoformat() if dday else None
            results.append(RawOpportunity(
                source_id=self.config.id,
                source_name=self.config.name,
                source_url=source_url,
                source_post_id=post_id,
                title=title,
                organizer=fields.get("organ", "") or self.config.name,
                summary=f"위비티 등록 분야: {category}" if category else "위비티 IT·게임 분야 공모전",
                body_text=category,
                source_kind=self.config.kind,
                source_priority=self.config.priority,
                recruit_end=recruit_end,
                date_kind="exact" if recruit_end else "unknown",
                original_category=category,
                collected_at=now.isoformat(timespec="seconds"),
            ))
        return results
