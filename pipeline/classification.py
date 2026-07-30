from __future__ import annotations

import re
from typing import Any

from pipeline.models import RawOpportunity, Relevance


LABELS = {
    "game": "게임",
    "indie": "인디",
    "ai": "AI",
    "software": "소프트웨어",
    "web_app": "웹·앱",
    "data": "데이터",
    "immersive": "XR·메타버스",
    "cloud_security": "클라우드·보안",
    "startup": "창업",
    "digital_content": "디지털 콘텐츠",
}
AUDIENCE_LABELS = {
    "university": "대학생",
    "youth": "청년",
    "developer": "개발자",
    "startup": "창업자·기업",
}


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").casefold()).strip()


def keyword_matches(text: str, words: list[str]) -> list[str]:
    lowered = normalized(text)
    matches: list[str] = []
    for word in words:
        needle = normalized(word)
        if not needle:
            continue
        if re.fullmatch(r"[a-z0-9][a-z0-9 .+_-]*", needle):
            found = re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", lowered)
        else:
            found = needle in lowered
        if found:
            matches.append(word)
    return matches


def classify(raw: RawOpportunity, taxonomy: dict[str, Any]) -> tuple[str, list[str], list[str], Relevance, bool]:
    title = normalized(raw.title)
    combined = normalized(" ".join([
        raw.title, raw.summary, raw.body_text, raw.original_category,
        raw.eligibility, raw.benefits,
    ]))

    primary_type = "other"
    type_score = 0
    for type_id, config in taxonomy.get("types", {}).items():
        matches = keyword_matches(combined, config.get("keywords", []))
        if matches:
            candidate = 20 if keyword_matches(title, config.get("keywords", [])) else 10
            if candidate > type_score:
                primary_type, type_score = type_id, candidate

    field_tags: list[str] = []
    title_field_hits: list[str] = []
    body_field_hits: list[str] = []
    for field_id, keywords in taxonomy.get("fields", {}).items():
        title_hits = keyword_matches(title, keywords)
        body_hits = keyword_matches(combined, keywords)
        if body_hits:
            field_tags.append(LABELS.get(field_id, field_id))
            body_field_hits.extend(body_hits)
        if title_hits:
            title_field_hits.extend(title_hits)

    audience_tags: list[str] = []
    for audience_id, keywords in taxonomy.get("audiences", {}).items():
        if keyword_matches(combined, keywords):
            audience_tags.append(AUDIENCE_LABELS.get(audience_id, audience_id))

    score = 0
    reasons: list[str] = []
    if title_field_hits:
        score += min(50, 35 + len(set(title_field_hits)) * 5)
        reasons.append(f"제목 핵심 키워드: {', '.join(sorted(set(title_field_hits))[:4])}")
    if body_field_hits:
        score += min(30, 15 + len(set(body_field_hits)) * 3)
        reasons.append(f"본문·분류 키워드: {', '.join(sorted(set(body_field_hits))[:4])}")
    if type_score:
        score += 12
        reasons.append(f"공고 유형: {primary_type}")
    if raw.source_kind == "specialist":
        score += 35
        reasons.append("IT·게임 전문 출처")
    elif raw.source_kind == "official" and field_tags:
        score += 10
        reasons.append("공식 전문기관 출처")
    category_format = any(phrase in normalized(raw.original_category) for phrase in (
        "게임/소프트웨어", "웹/모바일/it", "디지털 콘텐츠",
    ))
    strong_format = (
        any(phrase in combined for phrase in ("게임 출품", "게임 형태", "인터랙티브 콘텐츠", "디지털 콘텐츠"))
        or (primary_type == "hackathon" and type_score == 20)
    )
    if category_format:
        score += 55
        reasons.append("원본 분류상 게임·IT·디지털 콘텐츠로 참가 가능")
    elif strong_format:
        score += 15
        reasons.append("게임·디지털 콘텐츠 형태로 참가 가능")

    excluded = keyword_matches(combined, taxonomy.get("exclude_phrases", []))
    if excluded:
        score -= 55
        reasons.append(f"제외 문맥: {', '.join(excluded[:3])}")
    if not title_field_hits and not strong_format and not category_format and score >= 70:
        score = 69
        reasons.append("제목의 IT·게임 직접 근거 부족")
    score = max(0, min(100, score))
    decision = "publish" if score >= 70 else "review" if score >= 50 else "exclude"
    adjacent = primary_type == "employment" or (primary_type == "education" and raw.fee == "paid")
    return primary_type, field_tags, audience_tags, Relevance(score, reasons or ["관련성 근거 부족"], decision), adjacent
