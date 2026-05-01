"""
한국경제 뉴스 크롤러 (HTML 스크래핑)
실행 테스트: python -m scrapers.hankyung
"""
import logging
import re
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

SCRAPE_URLS = [
    "https://www.hankyung.com/finance",
    "https://www.hankyung.com/economy",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.hankyung.com/",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
}


def _parse_time(raw: str) -> datetime | None:
    now = datetime.now(config.KST)
    try:
        if "분 전" in raw:
            m = int(re.search(r"\d+", raw).group())
            return now - timedelta(minutes=m)
        if "시간 전" in raw:
            h = int(re.search(r"\d+", raw).group())
            return now - timedelta(hours=h)
        if "일 전" in raw:
            d = int(re.search(r"\d+", raw).group())
            return now - timedelta(days=d)
        for fmt in ["%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M", "%Y.%m.%d"]:
            try:
                return config.KST.localize(datetime.strptime(raw.strip()[:len(fmt)], fmt))
            except Exception:
                pass
    except Exception:
        pass
    return None


def _fetch_page(url: str) -> list[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("한국경제 페이지 수집 오류 (%s): %s", url, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    seen_urls: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/article/" not in href:
            continue

        full_url = href if href.startswith("http") else "https://www.hankyung.com" + href
        if full_url in seen_urls:
            continue

        # 제목 추출: 링크 텍스트 → 부모 h태그 순서로 시도
        title = a.get_text(strip=True)
        if len(title) < 10:
            parent = a.find_parent(["li", "div", "article"])
            if parent:
                h = parent.find(["h2", "h3", "h4", "strong"])
                if h:
                    title = h.get_text(strip=True)

        if len(title) < 10:
            continue

        # 날짜 추출: 가까운 날짜 요소 탐색
        published_at = datetime.now(config.KST)
        parent = a.find_parent(["li", "div", "article"])
        if parent:
            for t in parent.find_all(["time", "span"]):
                raw = t.get_text(strip=True)
                parsed = _parse_time(raw)
                if parsed:
                    published_at = parsed
                    break

        seen_urls.add(full_url)
        articles.append({
            "title": title,
            "summary": "",
            "url": full_url,
            "source": "한국경제",
            "published_at": published_at,
            "category": "",
        })

        if len(articles) >= config.MAX_ARTICLES_PER_SOURCE:
            break

    return articles


def fetch_hankyung_news() -> list[dict]:
    """한국경제 뉴스 수집"""
    all_articles = []

    for url in SCRAPE_URLS:
        all_articles.extend(_fetch_page(url))
        time.sleep(config.REQUEST_DELAY_SEC)

    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    logger.info("한국경제: %d개 기사 수집", len(unique))
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = fetch_hankyung_news()
    print(f"\n총 {len(results)}개 기사 수집됨\n")
    for i, a in enumerate(results[:5], 1):
        print(f"{i}. {a['title']}")
        print(f"   출처: {a['source']} | 시각: {a['published_at']}")
        print(f"   URL: {a['url']}\n")
