from datetime import datetime
from zoneinfo import ZoneInfo

from pipeline.collectors.dev_event import DevEventCollector
from pipeline.collectors.eventus import EventusCollector
from pipeline.collectors.html import StructuredHtmlCollector, parse_date
from pipeline.collectors.bizinfo import BizinfoCollector
from pipeline.collectors.kocca import KoccaCollector
from pipeline.collectors.linkareer import LinkareerCollector
from pipeline.collectors.thinkcontest import ThinkContestCollector
from pipeline.collectors.wevity import WevityCollector
from pipeline.config import SourceConfig
from pipeline.http import Response


NOW = datetime(2026, 7, 30, tzinfo=ZoneInfo("Asia/Seoul"))


class FakeClient:
    def __init__(self, pages): self.pages = pages
    def get(self, url, headers=None):
        return Response(url, 200, self.pages[url], "text/html")

    def post_json(self, url, payload, headers=None):
        return Response(url, 200, self.pages[url], "application/json")


def config(source_id="sample", mode="html"):
    return SourceConfig(source_id, "샘플", "specialist", 60, "fast", mode, "https://example.com/list", "https://example.com", True)


def test_json_ld_collector_contract():
    markup = '''<script type="application/ld+json">{"@type":"Event","name":"AI 게임 해커톤","url":"/event/1","organizer":{"name":"개발자협회"},"startDate":"2026-08-01","endDate":"2026-08-31","description":"AI 게임 개발자를 위한 해커톤입니다."}</script>'''
    items = StructuredHtmlCollector(config(), FakeClient({"https://example.com/list": markup})).collect(NOW)
    assert items[0].title == "AI 게임 해커톤"
    assert items[0].recruit_end == "2026-08-31"


def test_detail_title_removes_source_suffix():
    list_markup = '<a href="/event/1">AI 게임 해커톤 모집</a>'
    detail_markup = '<meta property="og:title" content="AI 게임 해커톤 | 샘플"><meta name="description" content="AI 게임 개발자를 위한 해커톤 행사입니다.">2026-08-01 ~ 2026-08-31'
    client = FakeClient({"https://example.com/list": list_markup, "https://example.com/event/1": detail_markup})
    item = StructuredHtmlCollector(config(), client).collect(NOW)[0]
    assert item.title == "AI 게임 해커톤"


def test_navigation_link_is_not_collected_as_an_opportunity():
    markup = '<a href="/guide">대회 참가 방법 안내</a>'
    collector = StructuredHtmlCollector(config(), FakeClient({"https://example.com/list": markup}))
    try:
        collector.collect(NOW)
    except Exception as error:
        assert "공고 링크" in str(error)
    else:
        raise AssertionError("탐색 링크가 공고로 수집되었습니다")


def test_generic_meta_title_falls_back_to_specific_list_title():
    list_markup = '<a href="/notice/42">AI 게임 제작지원 사업공고</a>'
    detail_markup = '<meta property="og:title" content="사업공고 | 사업공고 | 알림마당"><meta name="description" content="AI 게임 제작팀 지원사업입니다.">2026-08-01 ~ 2026-08-31'
    collector = StructuredHtmlCollector(config(), FakeClient({
        "https://example.com/list": list_markup,
        "https://example.com/notice/42": detail_markup,
    }))
    item = collector.collect(NOW)[0]
    assert item.title == "AI 게임 제작지원 사업공고"


def test_dev_event_markdown_contract():
    markdown = '''## `26년 08월`
* [게임 AI 해커톤](https://event.example.com)
  * 분류: `온라인`, `무료`, `대회`, `AI`
  * 주최: 테스트협회
  * 접수: 2026. 07. 20 ~ 2026. 08. 20
'''
    cfg = config("dev_event", "markdown")
    client = FakeClient({cfg.list_url: markdown})
    item = DevEventCollector(cfg, client).collect(NOW)[0]
    assert item.organizer == "테스트협회"
    assert item.recruit_end == "2026-08-20"


def test_invalid_calendar_date_is_rejected():
    assert parse_date("2026-02-30") is None


def test_eventus_embedded_public_search_contract():
    markup = '''<script>const app = { searchDataRaw: {"meta":{},"results":[{"id":{"raw":"42"},"subdomain":{"raw":"game-lab"},"title":{"raw":"AI 게임 개발 밋업"},"description":{"raw":"인디게임 개발자와 AI 기술을 나누는 행사"},"app_title":{"raw":"게임랩"},"category":{"raw":"IT/프로그래밍"},"category2":{"raw":"AI"},"event_type":{"raw":"강연/세미나"},"tags":{"raw":["게임","개발자"]},"register_start_date":{"raw":"2026-07-20T00:00:00+09:00"},"register_due_date":{"raw":"2026-08-20T23:59:00+09:00"},"start_date":{"raw":"2026-08-21T18:00:00+09:00"},"close_date":{"raw":"2026-08-21T21:00:00+09:00"},"area_detail":{"raw":"서울 강남구"},"event_system_type":{"raw":"offline"},"payway":{"raw":"false"}}]}, next: true };</script>'''
    cfg = config("eventus")
    item = EventusCollector(cfg, FakeClient({cfg.list_url: markup})).collect(NOW)[0]
    assert item.source_url == "https://event-us.kr/game-lab/event/42"
    assert item.organizer == "게임랩"
    assert item.recruit_end == "2026-08-20"
    assert item.mode == "offline"
    assert item.fee == "free"


def test_wevity_category_row_contract():
    cfg = config("wevity")
    url = "https://example.com/list?cidx=21&gbn=list&mode=soon&gp=1"
    markup = '''<li><div class="tit"><a href="?gbn=view&ix=42">게임 제작 공모전</a><div class="sub-tit">분야 : 게임/소프트웨어</div></div><div class="organ">게임재단</div><div class="day">D-10 <span>접수중</span></div></li>'''
    item = WevityCollector(cfg, FakeClient({url: markup})).collect(NOW, 1)[0]
    assert item.source_post_id == "42"
    assert item.original_category == "게임/소프트웨어"
    assert item.recruit_end == "2026-08-09"


def test_wevity_closed_row_uses_d_plus_deadline():
    cfg = config("wevity")
    markup = '''<li><div class="tit"><a href="?gbn=view&ix=43">지난 게임 공모전</a><div class="sub-tit">분야 : 게임/소프트웨어</div></div><div class="organ">게임재단</div><div class="day">D+10 <span>마감</span></div></li>'''
    item = WevityCollector(cfg, FakeClient({}))._parse_page(markup, cfg.list_url, NOW)[0]
    assert item.recruit_end == "2026-07-20"


def test_kocca_support_table_contract():
    cfg = config("kocca")
    url = "https://example.com/list?pageIndex=1"
    markup = '''<table><tr><td><span>모집공고</span></td><td><a href="/pims/view.do?intcNo=GAME1">게임 참가기업 모집</a></td><td>26.07.20</td><td>26.07.20 ~ 26.08.20</td><td>10</td></tr></table>'''
    item = KoccaCollector(cfg, FakeClient({url: markup})).collect(NOW, 1)[0]
    assert item.source_post_id == "GAME1"
    assert item.recruit_end == "2026-08-20"
    assert "디지털 콘텐츠" in item.original_category


def test_bizinfo_public_html_support_and_event_contract():
    cfg = SourceConfig("bizinfo", "기업마당", "government", 80, "slow", "html", "https://example.com/sii/siia/selectSIIA200View.do", "https://example.com", True)
    support = '''<tr><td>1</td><td>기술</td><td><a href="/sii/siia/selectSIIA200Detail.do?pblancId=P1" title="AI 게임 지원사업 페이지 이동">AI 게임 지원사업</a></td><td>2026-07-20 ~ 2026-08-20</td><td>부처</td><td>수행기관</td><td>2026-07-20</td><td>1</td></tr>'''
    event = '''<tr><td>1</td><td>전국</td><td><a href="/sie/siea/selectSIEA430Detail.do?eventInfoId=E1" title="AI 게임 행사 페이지로 이동">AI 게임 행사</a></td><td>2026-08-21 ~ 2026-08-21</td><td>행사기관</td><td>2026-07-20</td><td>1</td></tr>'''

    class SearchClient:
        def get(self, url, headers=None):
            return Response(url, 200, event if "SIEA430" in url else support, "text/html")

    items = BizinfoCollector(cfg, SearchClient()).collect(NOW, 2)
    assert {item.source_post_id for item in items} == {"P1", "E1"}


def test_thinkcontest_game_category_contract():
    cfg = config("thinkcontest")
    payload = '{"listJsonData":[{"contest_pk":42,"program_nm":"게임 제작 공모전","host_company":"게임사","accept_dt":"2026-07-20","finish_dt":"2026-08-20","contest_field_nm":"게임/소프트웨어","process":"ING"}]}'
    item = ThinkContestCollector(cfg, FakeClient({ThinkContestCollector.ENDPOINT: payload})).collect(NOW, 1)[0]
    assert item.source_post_id == "42"
    assert item.recruit_end == "2026-08-20"


def test_thinkcontest_keeps_recent_closed_record():
    cfg = config("thinkcontest")
    records = [{"contest_pk": 43, "program_nm": "이동 안내//지난 AI 게임 공모전", "host_company": "게임사", "finish_dt": "2026-07-20", "process": "END"}]
    item = ThinkContestCollector(cfg, FakeClient({}))._records(records, NOW, ended_only=True)[0]
    assert item.title == "지난 AI 게임 공모전"
    assert item.recruit_end == "2026-07-20"


def test_linkareer_server_state_contract():
    cfg = config("linkareer")
    url = "https://example.com/list?page=1"
    markup = '''<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"__APOLLO_STATE__":{"Activity:42":{"id":"42","title":"AI 게임 해커톤","organizationName":"NHN","recruitCloseAt":1788102000000}}}}}</script>'''
    item = LinkareerCollector(cfg, FakeClient({url: markup})).collect(NOW, 1)[0]
    assert item.source_post_id == "42"
    assert item.organizer == "NHN"
