from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline.collectors.registry import create_collector
from pipeline.config import ROOT, SourceConfig, load_local_env, load_sources, load_taxonomy
from pipeline.dedupe import deduplicate
from pipeline.history import clone_opportunity, reconcile_history
from pipeline.models import CrawlStatus, Opportunity
from pipeline.normalize import normalize
from pipeline.overrides import apply_overrides, manual_items
from pipeline.storage import read_payload, write_all


KST = ZoneInfo("Asia/Seoul")


def selected_sources(sources: list[SourceConfig], schedule: str, names: set[str] | None) -> list[SourceConfig]:
    return [
        source for source in sources
        if source.enabled
        and (schedule == "all" or source.schedule == schedule)
        and (not names or source.id in names)
    ]


def previous_statuses(output_dir: Path) -> dict[str, dict]:
    payload = read_payload(output_dir / "sources.json")
    return {item["source_id"]: item for item in payload.get("items", [])}


def previous_opportunities(output_dir: Path) -> list[Opportunity]:
    items: list[Opportunity] = []
    for filename in ("active.json", "undated.json", "closed.json", "review.json"):
        for data in read_payload(output_dir / filename).get("items", []):
            item = clone_opportunity(data)
            if item:
                items.append(item)
    return items


def run_pipeline(
    output_dir: Path | None = None,
    schedule: str = "all",
    names: set[str] | None = None,
    limit: int = 100,
    now: datetime | None = None,
) -> tuple[list[Opportunity], list[CrawlStatus]]:
    current = now or datetime.now(KST)
    output = output_dir or ROOT / "public" / "data"
    load_local_env()
    sources, _ = load_sources()
    enabled_ids = {source.id for source in sources if source.enabled}
    taxonomy = load_taxonomy()
    old_statuses = previous_statuses(output)
    old_opportunities = previous_opportunities(output)
    opportunities: list[Opportunity] = []
    statuses: list[CrawlStatus] = []

    env_names = {name.strip() for name in os.environ.get("QUESTBOARD_SOURCES", "").split(",") if name.strip()}
    effective_names = names or env_names or None
    for source in selected_sources(sources, schedule, effective_names):
        started = datetime.now(KST)
        previous = old_statuses.get(source.id, {})
        try:
            raw_items = create_collector(source).collect(current, limit=limit)
            normalized_items = [normalize(item, taxonomy, current) for item in raw_items]
            opportunities.extend(normalized_items)
            published = sum(item.relevance.decision == "publish" for item in normalized_items)
            review = sum(item.relevance.decision == "review" for item in normalized_items)
            statuses.append(CrawlStatus(
                source_id=source.id,
                source_name=source.name,
                status="success",
                started_at=started.isoformat(timespec="seconds"),
                finished_at=datetime.now(KST).isoformat(timespec="seconds"),
                collected_count=len(raw_items),
                published_count=published,
                review_count=review,
                consecutive_failures=0,
                last_success_at=current.isoformat(timespec="seconds"),
            ))
        except Exception as error:
            statuses.append(CrawlStatus(
                source_id=source.id,
                source_name=source.name,
                status="failed",
                started_at=started.isoformat(timespec="seconds"),
                finished_at=datetime.now(KST).isoformat(timespec="seconds"),
                consecutive_failures=int(previous.get("consecutive_failures", 0)) + 1,
                last_success_at=previous.get("last_success_at"),
                error=str(error)[:500],
            ))

    # Preserve untouched data, and keep the last good copy when a selected source fails.
    selected_ids = {source.id for source in selected_sources(sources, schedule, effective_names)}
    failed_ids = {status.source_id for status in statuses if status.status == "failed"}
    for item in old_opportunities:
        source_ids = {record.source_id for record in item.sources}
        active_source_ids = source_ids & enabled_ids
        if active_source_ids and (active_source_ids.isdisjoint(selected_ids) or active_source_ids & failed_ids):
            opportunities.append(item)
    for source_id, item in old_statuses.items():
        if source_id in enabled_ids and source_id not in selected_ids:
            statuses.append(CrawlStatus(**{key: value for key, value in item.items() if key in CrawlStatus.__dataclass_fields__}))

    opportunities.extend(manual_items(taxonomy, current))
    items = reconcile_history(apply_overrides(deduplicate(opportunities), now=current), old_opportunities, current)
    current_stamp = current.isoformat(timespec="seconds")
    for status in statuses:
        if status.status != "success":
            continue
        source_items = [item for item in items if status.source_id in {source.source_id for source in item.sources}]
        status.new_count = sum(item.first_seen_at == current_stamp for item in source_items)
        status.changed_count = sum(item.last_changed_at == current_stamp for item in source_items)
    write_all(output, items, statuses, current)
    return items, statuses
