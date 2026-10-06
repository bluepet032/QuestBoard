from pipeline.alerts import source_alerts


def status(source_id: str, state: str, failures: int, collected: int = 20, previous: int | None = 20) -> dict:
    return {
        "source_id": source_id, "source_name": source_id, "status": state,
        "finished_at": "2026-10-06T10:00:00+09:00", "consecutive_failures": failures,
        "collected_count": collected, "previous_collected_count": previous,
        "error": "요청 실패" if state == "failed" else None,
    }


def titles(items: list[dict]) -> list[str]:
    return [item["title"] for item in items]


def test_sources_at_threshold_need_an_issue_and_successes_can_close_one():
    alerts = source_alerts({"items": [
        status("bizinfo", "failed", 2),
        status("kocca", "failed", 1),
        status("wevity", "success", 0),
    ]})

    assert titles(alerts["failing"]) == ["[수집 실패] bizinfo"]
    assert "2회 연속 실패" in alerts["failing"][0]["body"]
    assert titles(alerts["recovered"]) == ["[수집 실패] wevity", "[수집 급감] wevity"]


def test_failures_below_threshold_neither_open_nor_close_issues():
    alerts = source_alerts({"items": [status("kocca", "failed", 1)]})

    assert alerts == {"failing": [], "recovered": []}


def test_sharp_drop_against_previous_success_opens_an_issue():
    alerts = source_alerts({"items": [
        status("wevity", "success", 0, collected=40, previous=100),
        status("nipa", "success", 0, collected=4, previous=8),
        status("dacon", "success", 0, collected=60, previous=100),
    ]})

    assert titles(alerts["failing"]) == ["[수집 급감] wevity"]
    assert "100건에서 40건" in alerts["failing"][0]["body"]
    assert "[수집 급감] nipa" in titles(alerts["recovered"])
    assert "[수집 급감] dacon" in titles(alerts["recovered"])


def test_drop_checks_can_be_skipped_for_partial_manual_runs():
    alerts = source_alerts({"items": [status("wevity", "success", 0, collected=5, previous=100)]}, check_drops=False)

    assert titles(alerts["failing"]) == []
    assert titles(alerts["recovered"]) == ["[수집 실패] wevity"]
