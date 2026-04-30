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

    print(f"[DEBUG] 사용 중인 database_id: {self.database_id[:8]}...")  # 추가

    db_properties = self._get_database_properties()

    print(f"[DEBUG] DB 속성 목록: {list(db_properties.keys())}")  # 추가

    # 실제 title 타입 속성 이름 찾기
    title_prop_name = None
    for prop_name, prop_info in db_properties.items():
        if prop_info.get('type') == 'title':
            title_prop_name = prop_name
            break

    if title_prop_name is None:
        title_prop_name = "Title"
        print(f"title 속성을 찾지 못해 기본값 사용: {title_prop_name}")
    else:
        print(f"사용할 title 속성명: {title_prop_name}")

    prop_names = list(db_properties.keys())

    for item in news_items:
        properties = {
            title_prop_name: {
                "title": [{"text": {"content": f"[{item.region}] {item.title}"}}]
            }
        }

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
            print(f"[DEBUG] 시도한 properties 키: {list(properties.keys())}")  # 추가


    def _get_database_properties(self):
        try:
            db = self.client.databases.retrieve(database_id=self.database_id)
            return db.get('properties', {})
        except Exception as e:
            print(f"데이터베이스 속성 조회 실패: {e}")
            return {}
