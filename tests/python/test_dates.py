from datetime import datetime
from zoneinfo import ZoneInfo

from pipeline.dates import status_for


KST = ZoneInfo("Asia/Seoul")


def test_date_status_boundaries():
    now = datetime(2026, 7, 30, 12, tzinfo=KST)
    assert status_for("2026-08-01", "2026-08-06", "exact", now) == ("upcoming", 7)
    assert status_for("2026-07-01", "2026-08-02", "exact", now) == ("urgent", 3)
    assert status_for("2026-07-01", "2026-07-30", "exact", now) == ("today", 0)
    assert status_for("2026-07-01", "2026-07-29", "exact", now) == ("closed", -1)
    assert status_for(None, None, "ongoing", now) == ("ongoing", None)
    assert status_for(None, None, "unknown", now) == ("unknown", None)

