from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pipeline.collectors.base import Collector, CollectorStructureError
from pipeline.models import RawOpportunity


NEXT_DATA_RE = re.compile(r'<script\s+id=["\']__NEXT_DATA__["\'][^>]*>(?P<data>.*?)</script>', re.I | re.S)


def _page_url(url: str, page: int) -> str:
    parts = urlsplit(url)
    query = {key: values[-1] for key, values in parse_qs(parts.query).items()}
    query["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


class LinkareerCollector(Collector):
    """Read Linkareer's public server-rendered Apollo state without detail-page fan-out."""

    def collect(self, now: datetime, limit: int = 30) -> list[RawOpportunity]:
        results: list[RawOpportunity] = []
        seen: set[str] = set()
        max_pages = max(2, (limit + 19) // 20 + 1)
        for page in range(1, max_pages + 1):
            response = self.client.get(_page_url(self.config.list_url, page))
            page_items = self._parse_page(response.text, now)
            new_items = [item for item in page_items if item.source_post_id not in seen]
            if not new_items:
                break
            for item in new_items:
                seen.add(item.source_post_id or item.source_url)
                results.append(item)
            if len(results) >= limit:
                return results[:limit]
        if not results:
            raise CollectorStructureError("링커리어 공개 목록 상태에서 공모전 항목을 찾지 못했습니다")
        return results[:limit]

    def _parse_page(self, markup: str, now: datetime) -> list[RawOpportunity]:
        match = NEXT_DATA_RE.search(markup)
        if not match:
            return []
        try:
            document = json.loads(match.group("data"))
            props = document["props"]
            page_props = props.get("pageProps", {})
            state = page_props.get("__APOLLO_STATE__") or props.get("apolloState")
            if not isinstance(state, dict):
                return []
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
        results: list[RawOpportunity] = []
        for key, value in state.items():
            if not key.startswith("Activity:") or not isinstance(value, dict) or not value.get("title"):
                continue
            post_id = str(value.get("id") or key.partition(":")[2])
            end_ms = value.get("recruitCloseAt")
            end = datetime.fromtimestamp(end_ms / 1000, tz=now.tzinfo).date().isoformat() if isinstance(end_ms, (int, float)) else None
            results.append(RawOpportunity(
                source_id=self.config.id,
                source_name=self.config.name,
                source_url=f"https://linkareer.com/activity/{post_id}",
                source_post_id=post_id,
                title=str(value["title"]),
                organizer=str(value.get("organizationName") or self.config.name),
                summary="링커리어 공개 공모전 목록",
                body_text=str(value["title"]),
                source_kind=self.config.kind,
                source_priority=self.config.priority,
                recruit_end=end,
                date_kind="exact" if end else "unknown",
                collected_at=now.isoformat(timespec="seconds"),
            ))
        return results
