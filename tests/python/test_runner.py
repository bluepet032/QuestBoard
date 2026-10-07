import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline import runner
from pipeline.models import RawOpportunity


class FakeCollector:
    def __init__(self, count: int | None):
        self.count = count

    def collect(self, now, limit=150):
        if self.count is None:
            raise RuntimeError("요청 실패")
        return [RawOpportunity(
            source_id="wevity", source_name="위비티", source_url=f"https://example.com/{index}",
            title=f"AI 게임 공모전 {index}", recruit_end="2026-12-31", date_kind="exact",
        ) for index in range(self.count)]


def run_once(monkeypatch, output: Path, count: int | None, day: int):
    monkeypatch.setattr(runner, "create_collector", lambda source: FakeCollector(count))
    runner.run_pipeline(output_dir=output, names={"wevity"}, now=datetime(2026, 10, day, 3, tzinfo=ZoneInfo("Asia/Seoul")))
    items = json.loads((output / "sources.json").read_text(encoding="utf-8"))["items"]
    return next(item for item in items if item["source_id"] == "wevity")


def test_previous_collected_count_tracks_the_last_successful_run(monkeypatch, tmp_path: Path):
    output = tmp_path / "data"

    first = run_once(monkeypatch, output, 12, 1)
    second = run_once(monkeypatch, output, 5, 2)
    failed = run_once(monkeypatch, output, None, 3)
    recovered = run_once(monkeypatch, output, 11, 4)

    assert first["previous_collected_count"] is None
    assert second["previous_collected_count"] == 12
    assert failed["previous_collected_count"] == 5
    assert recovered["previous_collected_count"] == 5


def test_facet_coverage_is_recorded_and_kept_as_baseline_through_failures(monkeypatch, tmp_path: Path):
    output = tmp_path / "data"

    first = run_once(monkeypatch, output, 4, 1)
    failed = run_once(monkeypatch, output, None, 2)
    recovered = run_once(monkeypatch, output, 4, 3)

    assert set(first["facet_coverage"]) == {"region", "mode", "fee", "audience", "prize"}
    assert first["previous_facet_coverage"] is None
    assert failed["facet_coverage"] is None
    assert failed["previous_facet_coverage"] == first["facet_coverage"]
    assert recovered["previous_facet_coverage"] == first["facet_coverage"]
