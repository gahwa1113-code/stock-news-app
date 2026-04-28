# 이 파일은 뉴스 출처, 요청 시간, 키워드, Notion 설정 등을 담고 있습니다.
import os
from dotenv import load_dotenv

load_dotenv()

settings = {
    "domestic_news_url": "https://finance.naver.com/news/",
    "overseas_news_url": "https://www.investing.com/news/",
    "news_per_region": 5,
    "request_delay_seconds": 1.5,
    "important_keywords": [
        "금리", "환율", "코스피", "코스닥", "실적", "공시", "미국", "FED", "CPI", "나스닥", "S&P500", "원/달러", "테슬라", "애플", "엔비디아"
    ],
    "notion_database_id": os.getenv("NOTION_DATABASE_ID", ""),
}
