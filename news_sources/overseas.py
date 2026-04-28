# 이 파일은 Investing.com에서 해외 뉴스 제목과 링크를 수집합니다.

import time
import requests
import feedparser
from bs4 import BeautifulSoup
from config import settings
from utils import NewsItem


def fetch_overseas_news() -> list[NewsItem]:
    url = settings["overseas_news_url"]
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.investing.com/",
    })

    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        items = []

        news_elements = soup.select("article")
        for element in news_elements[:15]:
            title_tag = element.select_one("a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href")
            if link and not link.startswith("http"):
                link = f"https://www.investing.com{link}"
            items.append(NewsItem(title=title, summary="", url=link, source="Investing.com", region="해외"))
            if len(items) >= settings["news_per_region"] * 2:
                break

        if items:
            time.sleep(settings["request_delay_seconds"])
            return items
    except requests.RequestException:
        pass

    return fetch_overseas_news_rss()


def fetch_overseas_news_rss() -> list[NewsItem]:
    rss_url = "https://www.investing.com/rss/news.rss"
    feed = feedparser.parse(rss_url)
    items = []

    for entry in feed.entries[:settings["news_per_region"] * 2]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        items.append(NewsItem(title=title, summary=summary, url=link, source="Investing.com RSS", region="해외"))

    time.sleep(settings["request_delay_seconds"])
    return items
