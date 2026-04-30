# Notion 데이터베이스에 뉴스를 저장하고, Gemini AI로 요약을 생성합니다
import os
import time
import requests as r
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI
from utils import NewsItem
from config import settings

load_dotenv()


def _generate_summary(title: str, original_summary: str) -> str:
    """Gemini API로 투자자용 AI 요약 2~3문장 생성"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return original_summary

    try:
        client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )
        prompt = (
            f"다음 뉴스를 주식 투자자 관점에서 2~3문장으로 한국어로 요약해주세요.\n"
            f"제목: {title}\n내용: {original_summary}"
        )
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI 요약 실패: {e}")
        return original_summary


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
        self.token = token

    def _get_db_props(self) -> set:
        """DB에 존재하는 속성 이름 목록 반환"""
        try:
            resp = r.get(
                f"https://api.notion.com/v1/databases/{self.database_id}",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Notion-Version": "2022-06-28"
                }
            )
            return set(resp.json().get("properties", {}).keys())
        except Exception as e:
            print(f"DB 속성 조회 실패: {e}")
            return set()

    def save_news_items(self, news_items: list[NewsItem]):
        today = datetime.now().date().isoformat()
        db_props = self._get_db_props()
        print(f"DB 속성 목록: {db_props}")

        for item in news_items:
            print(f"저장 중: [{item.region}] {item.title[:30]}...")

            # Gemini AI 요약 생성
            ai_summary = _generate_summary(item.title, item.summary)
            time.sleep(1)

            properties = {
                "Title": {
                    "title": [{"text": {"content": f"[{item.region}] {item.title}"}}]
                },
                "Date": {"date": {"start": today}},
            }

            if "Region" in db_props:
                properties["Region"] = {"select": {"name": item.region}}
            if "Summary" in db_props:
                properties["Summary"] = {
                    "rich_text": [{"text": {"content": ai_summary[:2000]}}]
                }
            if "URL" in db_props:
                properties["URL"] = {"url": item.url}
            if "Source" in db_props:
                properties["Source"] = {
                    "rich_text": [{"text": {"content": item.source}}]
                }

            try:
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                )
                print(f"성공: [{item.region}] {item.title}")
            except Exception as e:
                print(f"실패: {e}")
