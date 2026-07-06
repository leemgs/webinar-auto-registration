"""쉐어드IT (sharedit.co.kr) scraper.

The site returns HTTP 402 to plain HTTP clients, so it must be fetched with a
real browser (handled by the shared Browser). Parsing is generic card-based.
"""
from __future__ import annotations

from .base import BaseScraper


class Scraper(BaseScraper):
    CARD_SELECTORS = [
        ".webinar-list li",
        ".webinar_list li",
        ".list-webinar .item",
        ".card",
        "article",
    ]

    def parse(self, html):
        soup = self.soup(html)
        cards = self.select_cards(soup, self.CARD_SELECTORS)
        if not cards:
            cards = [li for li in soup.select("li, article") if li.select_one("a[href]") and li.select_one("img")]
        return self.cards_to_webinars(
            cards,
            title_sel="h3, .tit, .title, strong, .subject",
            host_sel=".host, .company, .org",
        )
