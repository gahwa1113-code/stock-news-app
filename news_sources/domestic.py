# 국내 경제 뉴스를 네이버 금융 스크래핑 + RSS 피드로 수집합니다
import re
import time
import requests
import feedparser
from bs4 import BeautifulSoup
from config import settings
from utils import NewsItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DOMESTIC_RSS_FEEDS = [
    ("https://www.yna.co.kr/rss/economy.xml", "연합뉴스"),
    ("https://rss.hankyung.com/finance/main.xml", "한국경제"),
]


def _fetch_naver_finance() -> list[NewsItem]:
    """네이버 금융 뉴스 페이지 스크래핑"""
    items = []
    urls = [
        "https://finance.naver.com/news/mainnews.naver",
        "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = "euc-kr"
            soup = BeautifulSoup(resp.text, "html.parser")

            for item in soup.select("ul.newsList li"):
                title_tag = item.select_one("dd.articleSubject a")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")
                link = href if href.startswith("http") else "https://finance.naver.com" + href

                summary_tag = item.select_one("dd.articleSummary")
                if summary_tag:
                    for span in summary_tag.find_all("span"):
                        span.decompose()
                    summary = summary_tag.get_text(strip=True)
                else:
                    summary = ""

                if title:
                    items.append(NewsItem(
                        title=title,
                        summary=summary,
                        url=link,
                        source="네이버금융",
                        region="국내"
                    ))

            time.sleep(settings["request_delay_seconds"])
        except Exception as e:
            print(f"네이버 금융 수집 실패 ({url}): {e}")

    print(f"네이버 금융: {len(items)}개 수집")
    return items


def _fetch_rss_feeds() -> list[NewsItem]:
    """연합뉴스, 한국경제 RSS 수집"""
    items = []
    for rss_url, source_name in DOMESTIC_RSS_FEEDS:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()[:300]

                if not title:
                    continue
                items.append(NewsItem(
                    title=title,
                    summary=summary or "요약 없음",
                    url=link,
                    source=source_name,
                    region="국내"
                ))
        except Exception as e:
            print(f"RSS 수집 실패 ({source_name}): {e}")
        time.sleep(settings["request_delay_seconds"])

    print(f"RSS 피드: {len(items)}개 수집")
    return items


def fetch_domestic_news() -> list[NewsItem]:
    items = []
    seen_urls = set()

    for item in _fetch_naver_finance() + _fetch_rss_feeds():
        if item.url not in seen_urls and item.title:
            seen_urls.add(item.url)
            items.append(item)

    print(f"국내 뉴스 총 {len(items)}개 수집 완료")
    return items
