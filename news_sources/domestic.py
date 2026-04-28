# 이 파일은 Naver 경제 뉴스에서 국내 뉴스 제목과 링크를 수집합니다.

import time
import requests
from bs4 import BeautifulSoup
from config import settings
from utils import NewsItem


def fetch_domestic_news() -> list[NewsItem]:
    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=101"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items = []

    news_elements = soup.select("div.newsflash_body > ul.type06_headline li")
    for element in news_elements:
        if len(items) >= settings["news_per_region"]:
            break
        link_tag = element.select_one("a")
        if not link_tag:
            continue
        title = link_tag.get_text(strip=True)
        link = link_tag.get("href")
        if not title:
            continue
        items.append(NewsItem(title=title, summary="", url=link, source="Naver Economics", region="국내"))

    time.sleep(settings["request_delay_seconds"])
    return items
