# Notion에 하루 1개의 브리핑 페이지를 생성합니다
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

def _build_blocks(domestic: list, overseas: list) -> list:
    """Notion 페이지 본문 블록 생성"""

    def heading2(text):
        return {"object": "block", "type": "heading_2", "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }}

    def heading3(text):
        return {"object": "block", "type": "heading_3", "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }}

    def bullet(text):
        return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }}

    def link_bullet(text, url):
        return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text, "link": {"url": url}}}]
        }}

    def divider():
        return {"object": "block", "type": "divider", "divider": {}}

    blocks = []

    # 국내 뉴스
    blocks.append(heading2("🇰🇷 국내 증시 요약"))
    blocks.append(divider())
    for i, (item, summary) in enumerate(domestic, 1):
        blocks.append(heading3(f"[{i}] {item.title}"))
        blocks.append(bullet(f"   - {summary}"))
        blocks.append(link_bullet(f"   원문 링크: {item.url}", item.url))

    blocks.append(divider())

    # 해외 뉴스
    blocks.append(heading2("🌎 해외 증시 요약"))
    blocks.append(divider())
    for i, (item, summary) in enumerate(overseas, 1):
        blocks.append(heading3(f"[{i}] {item.title}"))
        blocks.append(bullet(f"   - {summary}"))
        blocks.append(link_bullet(f"   원문 링크: {item.url}", item.url))

    blocks.append(divider())

    # 주요 지표
    blocks.append(heading2("💹 오늘의 주요 지표"))
    blocks.append(divider())
    blocks.append(bullet("코스피 종가: -"))
    blocks.append(bullet("나스닥 종가: -"))
    blocks.append(bullet("원/달러 환율: -"))
    blocks.append(bullet("비트코인: -"))

    return blocks

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

    def save_briefing(self, domestic: list[NewsItem], overseas: list[NewsItem]):
        """국내/해외 뉴스를 하루 1개 브리핑 페이지로 저장"""
        now = datetime.now()
        today = now.date().isoformat()
        title = f"📅 {now.year}년 {now.month}월 {now.day}일 아침 브리핑"

        # AI 요약 생성
        print("AI 요약 생성 중...")
        domestic_pairs = []
        for item in domestic:
            summary = _generate_summary(item.title, item.summary)
            domestic_pairs.append((item, summary))
            time.sleep(1)

        overseas_pairs = []
        for item in overseas:
            summary = _generate_summary(item.title, item.summary)
            overseas_pairs.append((item, summary))
            time.sleep(1)

        # 페이지 본문 블록 생성
        blocks = _build_blocks(domestic_pairs, overseas_pairs)

        # Notion 페이지 생성
        properties = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": today}},
        }

        try:
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=blocks[:100],
            )
            print(f"성공: 브리핑 페이지 생성 완료")
            print(f"URL: {page.get('url', '')}")
        except Exception as e:
            print(f"실패: {e}")
