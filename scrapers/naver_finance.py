"""
네이버 증권 뉴스 크롤러
실행 테스트: python -m scrapers.naver_finance
"""
import logging
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _parse_naver_time(raw: str) -> datetime | None:
    """네이버 증권 날짜 문자열 → datetime(KST) 변환"""
    raw = raw.strip()
    now = datetime.now(config.KST)
    try:
        if "분 전" in raw:
            minutes = int(raw.replace("분 전", "").strip())
            return now - timedelta(minutes=minutes)
        if "시간 전" in raw:
            hours = int(raw.replace("시간 전", "").strip())
            return now - timedelta(hours=hours)
        if "일 전" in raw:
            days = int(raw.replace("일 전", "").strip())
            return now - timedelta(days=days)
        # "2026-04-28 22:01:09" 형식 (span.wdate)
        if len(raw) == 19 and raw[4] == "-":
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            return config.KST.localize(dt)
        # "2026.04.29 07:00" 형식
        dt = datetime.strptime(raw, "%Y.%m.%d %H:%M")
        return config.KST.localize(dt)
    except Exception:
        return None


def _is_recent(dt: datetime | None) -> bool:
    if dt is None:
        return False
    now = datetime.now(config.KST)
    cutoff = now - timedelta(hours=config.NEWS_WINDOW_HOURS)
    if dt.tzinfo is None:
        dt = config.KST.localize(dt)
    return dt >= cutoff


def _scrape_naver_url(url: str) -> list[dict]:
    """단일 네이버 증권 URL에서 기사 파싱"""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    resp.encoding = "euc-kr"
    soup = BeautifulSoup(resp.text, "html.parser")

    items = soup.select("ul.newsList li.block1")
    if not items:
        items = soup.select("ul.newsList li")

    articles = []
    for item in items:
        title_tag = item.select_one("dd.articleSubject a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        href = title_tag.get("href", "")
        article_url = (
            href if href.startswith("http")
            else "https://finance.naver.com" + href
        )

        time_tag = item.select_one("span.wdate")
        raw_time = time_tag.get_text(strip=True) if time_tag else ""
        published_at = _parse_naver_time(raw_time)

        if not _is_recent(published_at):
            continue

        summary_tag = item.select_one("dd.articleSummary")
        if summary_tag:
            for span in summary_tag.find_all("span"):
                span.decompose()
            summary = summary_tag.get_text(strip=True)
        else:
            summary = ""

        articles.append({
            "title": title,
            "summary": summary,
            "url": article_url,
            "source": "네이버증권",
            "published_at": published_at,
            "category": "",
        })

    return articles


def fetch_naver_news() -> list[dict]:
    """네이버 증권 메인 뉴스 수집 (페이지네이션 포함)"""
    seen_urls = set()
    articles = []

    # 메인 페이지
    try:
        for a in _scrape_naver_url(config.NAVER_MAIN_URL):
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                articles.append(a)
        time.sleep(config.REQUEST_DELAY_SEC)
    except Exception as e:
        logger.warning("네이버 크롤링 오류 (%s): %s", config.NAVER_MAIN_URL, e)

    # 카테고리별 리스트 페이지
    for url in config.NAVER_LIST_URLS:
        if len(articles) >= config.MAX_ARTICLES_PER_SOURCE:
            break
        try:
            for a in _scrape_naver_url(url):
                if a["url"] not in seen_urls:
                    seen_urls.add(a["url"])
                    articles.append(a)
            time.sleep(config.REQUEST_DELAY_SEC)
        except Exception as e:
            logger.warning("네이버 크롤링 오류 (%s): %s", url, e)

    logger.info("네이버 증권: %d개 기사 수집", len(articles))
    return articles


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = fetch_naver_news()
    print(f"\n총 {len(results)}개 기사 수집됨\n")
    for i, a in enumerate(results[:5], 1):
        print(f"{i}. {a['title']}")
        print(f"   출처: {a['source']} | 시각: {a['published_at']}")
        print(f"   URL: {a['url']}\n")
