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
