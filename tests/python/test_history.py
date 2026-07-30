from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pipeline.config import load_taxonomy
from pipeline.history import reconcile_history
from pipeline.models import RawOpportunity
from pipeline.normalize import normalize


KST = ZoneInfo("Asia/Seoul")
OLD = datetime(2026, 7, 27, 9, 0, tzinfo=KST)
NOW = OLD + timedelta(days=3)


def make(now: datetime, *, end: str = "2026-08-31"):
    return normalize(RawOpportunity(
        source_id="fixture",
        source_name="테스트",
        source_url="https://example.com/notices/42",
        source_post_id="42",
        title="인디게임 제작지원 공모",
        organizer="게임재단",
        summary="인디게임 개발팀을 대상으로 제작비와 멘토링을 지원하는 공모 사업입니다.",
        recruit_end=end,
        date_kind="exact",
        collected_at=now.isoformat(timespec="seconds"),
    ), load_taxonomy(), now)


def test_same_item_keeps_first_seen_and_is_not_marked_changed():
    old = make(OLD)
    current = make(NOW)
    [result] = reconcile_history([current], [old], NOW)
    assert result.first_seen_at == old.first_seen_at
    assert result.last_changed_at is None
    assert result.change_flags == []


def test_material_change_sets_updated_timestamp_and_flags():
    old = make(OLD)
    current = make(NOW, end="2026-09-07")
    [result] = reconcile_history([current], [old], NOW)
    assert result.first_seen_at == old.first_seen_at
    assert result.last_changed_at == NOW.isoformat(timespec="seconds")
    assert result.change_flags == ["recruit_end"]
