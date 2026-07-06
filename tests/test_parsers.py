"""Offline parser tests — no browser required."""
from __future__ import annotations

from datetime import date

from webinar.scrapers.base import parse_date, parse_time
from webinar.scrapers import get_scraper
from webinar import prizes


REF = date(2026, 7, 6)


# --- date parsing ----------------------------------------------------------
def test_parse_date_iso():
    assert parse_date("2026-07-08") == date(2026, 7, 8)
    assert parse_date("2026.07.08") == date(2026, 7, 8)
    assert parse_date("2026년 7월 8일") == date(2026, 7, 8)


def test_parse_date_month_day():
    assert parse_date("7월 8일", ref=REF) == date(2026, 7, 8)
    assert parse_date("7/8", ref=REF) == date(2026, 7, 8)


def test_parse_date_dday():
    assert parse_date("D-2", ref=REF) == date(2026, 7, 8)


def test_parse_date_rollover():
    # a January date viewed in December should roll to next year
    assert parse_date("1월 5일", ref=date(2026, 12, 20)) == date(2027, 1, 5)


def test_parse_date_none():
    assert parse_date("no date here") is None


# --- time parsing ----------------------------------------------------------
def test_parse_time_variants():
    assert parse_time("14:00").hour == 14
    assert parse_time("오후 2시").hour == 14
    assert parse_time("오후 2시 30분").minute == 30
    assert parse_time("3:00 PM").hour == 15
    assert parse_time("오전 9시").hour == 9
    # Korean AM/PM with a colon (talkit's <time> format)
    t = parse_time("7월 9일(목) 오후 2:00~3:00")
    assert (t.hour, t.minute) == (14, 0)


# --- ddtube detail-link scraper -------------------------------------------
# The homepage links to /dNNNN/ detail pages (possibly multiple links per page,
# with/without trailing slash). parse() collects unique detail URLs; titles and
# dates are filled in later by _enrich() from each detail page.
DDTUBE_HTML = """
<html><body>
  <a href="/d2107" data-type="button">사전등록 바로가기 &gt;</a>
  <a href="/d2107/">[Synology] NVMe 스토리지 혁신</a>
  <a href="https://www.ddtube.co.kr/d2108">사전 등록</a>
  <a href="/mypage">마이페이지</a>
</body></html>
"""


def test_ddtube_collects_unique_detail_urls():
    scraper = get_scraper("ddtube", {"base_url": "https://www.ddtube.co.kr"})
    items = scraper.parse(DDTUBE_HTML)
    urls = {w.register_url for w in items}
    # d2107 appears twice (with/without slash) -> deduped to one canonical url
    assert urls == {
        "https://www.ddtube.co.kr/d2107/",
        "https://www.ddtube.co.kr/d2108/",
    }


# --- generic card scraper --------------------------------------------------
CARD_HTML = """
<html><body>
  <ul class="seminar_list">
    <li>
      <a href="/seminar/1"><strong class="tit">Enterprise AI Platform 전략</strong></a>
      <img src="/t.png"><span>2026.07.08 오후 3시</span>
      <span class="host">M Cloud Bridge</span>
    </li>
  </ul>
</body></html>
"""


def test_generic_card_scraper():
    scraper = get_scraper("allshowtv", {"base_url": "https://www.allshowtv.com"})
    items = scraper.parse(CARD_HTML)
    assert len(items) == 1
    w = items[0]
    assert w.title == "Enterprise AI Platform 전략"
    assert w.host == "M Cloud Bridge"
    assert w.start_kst.startswith("2026-07-08T15:00")
    assert w.url == "https://www.allshowtv.com/seminar/1"


# --- talkit anchor-card scraper -------------------------------------------
TALKIT_HTML = """
<html><body>
  <a href="/main/events/3697">
    <div><h3>미토스가 촉발한 AI 기반 Identity 공격 위험 [네오아이앤이]</h3>
    <time>7월 9일(목) 오후 2:00~3:00</time></div>
  </a>
  <a href="/main/webinars">웨비나</a>
</body></html>
"""


def test_talkit_scraper():
    scraper = get_scraper("talkit", {"base_url": "https://talkit.tv"})
    items = scraper.parse(TALKIT_HTML)
    assert len(items) == 1  # nav "웨비나" link filtered out
    w = items[0]
    assert w.url == "https://talkit.tv/main/events/3697"
    assert "미토스" in w.title
    assert w.start_kst.endswith("T14:00:00+09:00")


# --- allshowtv title tidying ----------------------------------------------
ALLSHOW_HTML = """
<html><body>
  <ul class="seminar_list">
    <li>
      <a href="/detail.html?idx=1735"><img src="/t.jpg">
      [엠클라우드브리지] Copilot 이후 기업은 왜 AI Platform 체계로 가는가?
      2026년 07월 08일(수) 15:00 ~ 16:00 D-2</a>
    </li>
  </ul>
</body></html>
"""


def test_allshowtv_title_and_host():
    scraper = get_scraper("allshowtv", {"base_url": "https://www.allshowtv.com"})
    items = scraper.parse(ALLSHOW_HTML)
    assert len(items) == 1
    w = items[0]
    assert w.host == "엠클라우드브리지"
    assert w.title == "Copilot 이후 기업은 왜 AI Platform 체계로 가는가?"
    assert w.start_kst.startswith("2026-07-08T15:00")


# --- prize extraction ------------------------------------------------------
def test_extract_prizes():
    text = "생방송 시청 후 설문 참여자 추첨하여 스타벅스 기프티콘을 드립니다."
    found = prizes.extract_prizes(text)
    types = {p.type for p in found}
    assert "survey" in types


def test_extract_prizes_empty():
    assert prizes.extract_prizes("그냥 일반 웨비나 소개 문구") == []
