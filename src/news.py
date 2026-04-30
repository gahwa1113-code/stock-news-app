import requests
import logging
from dataclasses import dataclass
from datetime import date
import html
from src.config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

logger = logging.getLogger(__name__)

NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"


@dataclass
class NewsItem:
    title: str
    url: str
    publisher: str
    published_at: str


def fetch_naver_news(stock_name: str, today: date, top_n: int = 10) -> list[NewsItem]:
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": stock_name,
        "display": min(top_n, 100),
        "sort": "date",
    }
    try:
        res = requests.get(NAVER_NEWS_URL, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])
        result = []
        for item in items[:top_n]:
            result.append(NewsItem(
                title=html.unescape(item.get("title", "").replace("<b>", "").replace("</b>", "")),
                url=item.get("originallink") or item.get("link", ""),
                publisher=item.get("description", "")[:20],
                published_at=item.get("pubDate", ""),
            ))
        logger.info(f"[{stock_name}] 뉴스 {len(result)}건 수집")
        return result
    except Exception as e:
        logger.error(f"뉴스 수집 실패 [{stock_name}]: {e}")
        return []
