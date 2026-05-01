"""
매일경제 뉴스 크롤러 (RSS 피드)
실행 테스트: python -m scrapers.mk
"""
import calendar
import logging
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; feedparser/6.0)"}


def _parse_published(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        ts = calendar.timegm(entry.published_parsed)
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(config.KST)
    return None


def _is_recent(dt: datetime | None) -> bool:
    if dt is None:
        return False
    return dt >= datetime.now(config.KST) - timedelta(hours=config.NEWS_WINDOW_HOURS)


def fetch_mk_news() -> list[dict]:
    """매일경제 RSS 피드에서 뉴스 수집"""
    all_articles = []

    for rss_url in config.MK_RSS_URLS:
        try:
            resp = requests.get(rss_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            for entry in feed.entries[:config.MAX_ARTICLES_PER_SOURCE]:
                published_at = _parse_published(entry)
                if not _is_recent(published_at):
                    continue
                all_articles.append({
                    "title": entry.get("title", "").strip(),
                    "summary": entry.get("summary", "").strip(),
                    "url": entry.get("link", ""),
                    "source": "매일경제",
                    "published_at": published_at,
                    "category": "",
                })
        except Exception as e:
            logger.warning("매일경제 RSS 수집 오류 (%s): %s", rss_url, e)

        time.sleep(config.REQUEST_DELAY_SEC)

    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    logger.info("매일경제: %d개 기사 수집", len(unique))
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = fetch_mk_news()
    print(f"\n총 {len(results)}개 기사 수집됨\n")
    for i, a in enumerate(results[:5], 1):
        print(f"{i}. {a['title']}")
        print(f"   출처: {a['source']} | 시각: {a['published_at']}")
        print(f"   URL: {a['url']}\n")
