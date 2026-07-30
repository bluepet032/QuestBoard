from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline.config import load_taxonomy
from pipeline.models import RawOpportunity
from pipeline.normalize import normalize
from pipeline.overrides import apply_overrides, manual_items


def test_manual_force_publish_and_exclusion(tmp_path: Path):
    (tmp_path / "opportunities.yml").write_text('''schema_version: 1
items:
  - id: manual-one
    title: 자유주제 디지털 콘텐츠 공모전
    source_url: https://example.com/manual
    organizer: 테스트기관
    summary: 게임 형태로 출품 가능한 자유주제 디지털 콘텐츠 공모전입니다.
    recruit_end: '2026-08-31'
    date_kind: exact
    force_publish: true
''', encoding="utf-8")
    (tmp_path / "overrides.yml").write_text("schema_version: 1\nitems: []\n", encoding="utf-8")
    (tmp_path / "exclusions.yml").write_text("schema_version: 1\nids: []\nsource_urls: []\n", encoding="utf-8")
    now = datetime(2026, 7, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    items = manual_items(load_taxonomy(), now, tmp_path)
    assert items[0].relevance.decision == "publish"
    assert apply_overrides(items, tmp_path) == items


def test_override_recalculates_deadline_and_review_score(tmp_path: Path):
    now = datetime(2026, 7, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    item = normalize(RawOpportunity(
        source_id="test",
        source_name="테스트",
        source_url="https://example.com/item",
        title="AI 게임 개발 공모전",
        summary="대학생 개발팀이 AI 게임을 제작해 출품하는 소프트웨어 공모전입니다.",
        recruit_end="2026-08-31",
        date_kind="exact",
    ), load_taxonomy(), now)
    (tmp_path / "overrides.yml").write_text('''schema_version: 1
items:
  - id: ''' + item.id + '''
    recruit_end: '2026-07-30'
    force_review: true
''', encoding="utf-8")
    (tmp_path / "exclusions.yml").write_text("schema_version: 1\nids: []\nsource_urls: []\n", encoding="utf-8")

    [result] = apply_overrides([item], tmp_path, now)

    assert result.status == "today"
    assert result.d_day == 0
    assert 50 <= result.relevance.score < 70
    assert result.relevance.decision == "review"
