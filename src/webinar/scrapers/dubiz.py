"""두비즈 (dubiz.co.kr) scraper — public listing; has a Q&A/경품 section."""
from __future__ import annotations

from .base import BaseScraper


class Scraper(BaseScraper):
    CARD_SELECTORS = [
        ".webinar_list li",
        ".seminar-list li",
        ".list-item",
        ".card",
        "article",
    ]

    def parse(self, html):
        soup = self.soup(html)
        cards = self.select_cards(soup, self.CARD_SELECTORS)
        if not cards:
            cards = [li for li in soup.select("li, article") if li.select_one("a[href]")]
        return self.cards_to_webinars(
            cards,
            title_sel="h3, .tit, .title, strong, .subject",
            host_sel=".host, .company, .org",
        )
