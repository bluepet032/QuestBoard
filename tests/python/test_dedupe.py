from datetime import datetime
from zoneinfo import ZoneInfo

from pipeline.config import load_taxonomy
from pipeline.dedupe import deduplicate
from pipeline.models import RawOpportunity
from pipeline.normalize import normalize


NOW = datetime(2026, 7, 30, tzinfo=ZoneInfo("Asia/Seoul"))


def make(source_id: str, url: str, priority: int, *, title: str = "2026 인디게임 제작지원 공모", organizer: str = "경기콘텐츠진흥원"):
    return normalize(RawOpportunity(
        source_id=source_id,
        source_name=source_id,
        source_url=url,
        title=title,
        organizer=organizer,
        summary="인디게임 개발팀을 대상으로 제작비를 지원하는 사업입니다.",
        source_kind="official" if priority > 80 else "aggregate",
        source_priority=priority,
        recruit_end="2026-08-31",
        date_kind="exact",
        collected_at=NOW.isoformat(),
    ), load_taxonomy(), NOW)


def test_duplicate_sources_merge_and_official_wins():
    merged = deduplicate([
        make("aggregate", "https://example.com/repost", 40),
        make("official", "https://official.example.com/post", 100),
    ])
    assert len(merged) == 1
    assert merged[0].source_name == "official"
    assert len(merged[0].sources) == 2


def test_duplicate_merge_keeps_score_and_decision_consistent():
    preferred = make("official", "https://official.example.com/post", 100)
    secondary = make("aggregate", "https://example.com/repost", 40)
    preferred.relevance.score = 40
    preferred.relevance.decision = "exclude"
    secondary.relevance.score = 75
    secondary.relevance.decision = "publish"

    [merged] = deduplicate([preferred, secondary])

    assert merged.relevance.score == 75
    assert merged.relevance.decision == "publish"


def test_cross_site_posts_merge_at_ninety_percent_title_similarity():
    merged = deduplicate([
        make("wevity", "https://wevity.example.com/42", 40, organizer="주최기관 미상"),
        make("official", "https://official.example.com/42", 100, title="2026 인디게임 제작지원 공모전", organizer="경기콘텐츠진흥원"),
    ])

    assert len(merged) == 1
    assert {source.source_id for source in merged[0].sources} == {"wevity", "official"}
