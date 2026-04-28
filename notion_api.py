# 이 파일은 Notion API를 사용하여 뉴스 데이터를 데이터베이스에 저장합니다.

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

    def save_news_items(self, news_items: list[NewsItem]):
        today = datetime.now().date().isoformat()

        # 데이터베이스 속성 확인
        db_properties = self._get_database_properties()

        # Title 속성이 있는지 확인
        has_title = any(info.get('type') == 'title' for info in db_properties.values())

        # properties가 없거나 Title 속성이 확인되지 않아도 시도
        # 실제 페이지 생성 테스트에서 Title 속성으로 성공했음
        if not has_title and len(db_properties) == 0:
            print("properties 정보가 없지만 Title 속성으로 저장 시도...")
            has_title = True

        if not has_title:
            print("경고: Notion 데이터베이스에 Title 속성이 없습니다.")
            print("  뉴스 저장을 건너뜁니다. Notion에서 Title 속성을 추가해주세요.")
            return  # 조용히 리턴

        for item in news_items:
            # Title 속성이 있으므로 저장 진행
            properties = {
                "Title": {
                    "title": [{"text": {"content": f"[{item.region}] {item.title}"}}]
                }
            }

            # 다른 속성들이 있으면 추가
            prop_names = list(db_properties.keys())
            if "Date" in prop_names:
                properties["Date"] = {"date": {"start": today}}

            if "Region" in prop_names:
                properties["Region"] = {"select": {"name": item.region}}

            if "Source" in prop_names:
                properties["Source"] = {"rich_text": [{"text": {"content": item.source}}]}

            if "URL" in prop_names:
                properties["URL"] = {"url": item.url}

            try:
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                )
                print(f"성공: 뉴스 저장 성공: [{item.region}] {item.title}")
            except Exception as e:
                print(f"실패: 뉴스 저장 실패: {e}")

    def _get_database_properties(self):
        """데이터베이스의 현재 속성들을 가져옵니다."""
        try:
            db = self.client.databases.retrieve(database_id=self.database_id)
            return db.get('properties', {})
        except:
            return {}
