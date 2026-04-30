import os
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from utils import NewsItem
from config import settings

load_dotenv()


class NotionClient:
    def __init__(self):
        token = os.getenv("NOTION_TOKEN")
        database_id = settings.get("notion_database_id") or os.getenv("NOTION_DATABASE_ID")

        if not token:
            raise ValueError("NOTION_TOKEN 환경 변수가 설정되지 않았습니다.")
        if not database_id:
            raise ValueError("Notion 데이터베이스 ID가 설정되지 않았습니다.")

        self.client = Client(auth=token)
        self.database_id = database_id
        print(f"[DEBUG] NotionClient 초기화 완료. DB ID: {self.database_id[:8]}...")

    def save_news_items(self, news_items: list[NewsItem]):
        today = datetime.now().date().isoformat()

        for item in news_items:
            properties = {
                "Title": {
                    "title": [{"text": {"content": f"[{item.region}] {item.title}"}}]
                },
                "Date": {
                    "date": {"start": today}
                }
            }

            try:
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                )
                print(f"성공: [{item.region}] {item.title}")
            except Exception as e:
                print(f"실패: {e}")
