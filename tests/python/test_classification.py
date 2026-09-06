from pipeline.classification import classify
from pipeline.config import load_taxonomy
from pipeline.models import RawOpportunity


def raw(**values):
    base = dict(source_id="test", source_name="테스트", source_url="https://example.com/1", title="테스트")
    base.update(values)
    return RawOpportunity(**base)


def test_direct_game_contest_is_published():
    primary, fields, audiences, relevance, adjacent = classify(raw(
        title="대학생 인디게임 개발 공모전",
        summary="게임 개발자가 팀으로 참여하는 소프트웨어 경진대회",
    ), load_taxonomy())
    assert primary == "contest"
    assert "게임" in fields and "인디" in fields
    assert "대학생" in audiences
    assert relevance.score >= 70
    assert relevance.decision == "publish"
    assert not adjacent


def test_promotional_event_is_excluded():
    _, _, _, relevance, _ = classify(raw(
        title="모바일 게임 경품 이벤트",
        summary="상품 할인 행사와 단순 체험단 모집",
    ), load_taxonomy())
    assert relevance.decision == "exclude"


def test_employment_is_adjacent():
    primary, _, _, _, adjacent = classify(raw(
        title="게임 클라이언트 개발자 신입 채용",
        summary="게임 프로그래밍 직무 채용",
    ), load_taxonomy())
    assert primary == "employment"
    assert adjacent


def test_short_english_keywords_require_word_boundaries():
    _, fields, _, relevance, _ = classify(raw(
        title="WITH WORSHIP CREATIVE TEAM",
        summary="청년들을 위한 찬양 집회와 공연",
        source_kind="specialist",
    ), load_taxonomy())
    assert "소프트웨어" not in fields
    assert "AI" not in fields
    assert relevance.decision == "exclude"


def test_non_game_ai_contest_is_excluded():
    primary, fields, _, relevance, _ = classify(raw(
        title="대학생 AI 영상 공모전",
        summary="대학생이 참여해 영상을 출품하는 공모전입니다.",
    ), load_taxonomy())
    assert primary == "contest"
    assert "AI" in fields
    assert relevance.score < 50
    assert relevance.decision == "exclude"


def test_non_game_ai_specialist_event_is_excluded():
    _, fields, _, relevance, _ = classify(raw(
        title="AIEngineering 소모임 - 실전 GenAI 애플리케이션 만들기",
        source_kind="specialist",
    ), load_taxonomy())
    assert "AI" in fields
    assert relevance.decision == "exclude"


def test_body_only_navigation_noise_cannot_auto_publish():
    _, _, _, relevance, _ = classify(raw(
        title="2026 대한민국 부동산 시장 흐름 이해",
        body_text="사이트 메뉴 AI IT 게임 데이터 공모전",
        source_kind="specialist",
    ), load_taxonomy())
    assert relevance.score <= 69
    assert relevance.decision != "publish"


def test_non_game_hackathon_is_excluded():
    primary, _, _, relevance, _ = classify(raw(
        title="공공데이터 활용 해커톤 참가자 모집",
        body_text="개발자와 기획자가 데이터 서비스를 만드는 행사",
        source_kind="specialist",
    ), load_taxonomy())
    assert primary == "hackathon"
    assert relevance.decision == "exclude"


def test_procurement_contract_is_excluded():
    _, _, _, relevance, _ = classify(raw(
        title="생성형 AI 콘텐츠 제작 서비스 공급 및 운영 용역",
        body_text="AI 시스템 개발 입찰 공고",
    ), load_taxonomy())
    assert relevance.decision == "exclude"


def test_broad_game_software_category_requires_review():
    _, fields, _, relevance, _ = classify(raw(
        title="제17회 국토기술 공모전",
        original_category="기획/아이디어, 게임/소프트웨어, 과학/공학",
    ), load_taxonomy())
    assert "게임" in fields
    assert relevance.decision == "review"


def test_game_company_support_is_published():
    primary, _, _, relevance, _ = classify(raw(
        title="2026 제작지원 사업 참가기업 모집",
        summary="프로젝트 제작비와 출시를 지원합니다.",
        eligibility="인디게임 개발팀과 게임기업",
        source_kind="official",
    ), load_taxonomy())
    assert primary == "support"
    assert relevance.decision == "publish"


def test_game_track_in_multi_format_contest_is_published():
    _, _, _, relevance, _ = classify(raw(
        title="대한민국 안전 AI 게임·영상 공모전",
        summary="게임 또는 영상 작품을 선택해 출품할 수 있습니다.",
    ), load_taxonomy())
    assert relevance.decision == "publish"


def test_esports_player_contest_is_excluded():
    _, _, _, relevance, _ = classify(raw(
        title="리그 오브 레전드 e스포츠 대회 선수 모집",
        summary="게임 경기 참가자를 모집합니다.",
        original_category="게임/소프트웨어",
    ), load_taxonomy())
    assert relevance.decision == "exclude"


def test_game_lecture_is_excluded_even_when_aggregate_category_says_contest():
    _, _, _, relevance, _ = classify(raw(
        title="게임기획 무료강의",
        summary="게임/소프트웨어 공모 분야에 등록된 온라인 교육입니다.",
        original_category="게임/소프트웨어",
    ), load_taxonomy())
    assert relevance.decision == "exclude"


def test_game_criticism_contest_is_excluded():
    _, _, _, relevance, _ = classify(raw(
        title="제5회 게임 비평 공모전",
        summary="게임에 관한 비평문을 제출합니다.",
    ), load_taxonomy())
    assert relevance.decision == "exclude"
