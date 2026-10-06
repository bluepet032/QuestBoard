import json
from pathlib import Path
from shutil import copytree

from pipeline.validate import validate_payloads


def test_committed_generated_data_is_valid():
    assert validate_payloads(Path("public/data")) == []


def test_invalid_public_summary_and_source_url_are_rejected(tmp_path: Path):
    data_dir = tmp_path / "data"
    copytree(Path("public/data"), data_dir)
    path = data_dir / "active.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["summary"] = "너무 짧음"
    payload["items"][0]["source_url"] = ""
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validate_payloads(data_dir)

    assert any("요약은 60~180자" in error for error in errors)
    assert any("대표 URL" in error for error in errors)


def test_source_body_text_in_public_data_is_rejected(tmp_path: Path):
    data_dir = tmp_path / "data"
    copytree(Path("public/data"), data_dir)
    path = data_dir / "active.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["classification_inputs"] = [{"body_text": "원문 본문 전체"}]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validate_payloads(data_dir)

    assert any("원문 본문 필드" in error for error in errors)


def test_field_tab_items_may_publish_below_the_it_threshold_but_need_a_known_domain(tmp_path: Path):
    data_dir = tmp_path / "data"
    copytree(Path("public/data"), data_dir)
    path = data_dir / "active.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["relevance"]["score"] = 10
    payload["items"][0]["domain"] = "design_media"
    payload["items"][1]["domain"] = "cooking"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validate_payloads(data_dir)

    assert not any("[0]: 공개 점수" in error for error in errors)
    assert any("[1]: 분야(domain)" in error for error in errors)
