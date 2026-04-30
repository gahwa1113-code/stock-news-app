"""
Notion 데이터베이스에 브리핑 페이지 저장
실행 테스트: python -m storage.notion_writer
"""
import logging
import os
import requests as req
from datetime import datetime

from notion_client import Client
from dotenv import load_dotenv
load_dotenv(override=True)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def _get_notion_client():
    return Client(auth=os.environ["NOTION_API_KEY"])


def _get_headers():
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _archive_existing(date_str: str):
    """같은 날짜의 기존 페이지를 아카이브"""
    database_id = os.environ["NOTION_DATABASE_ID"]
    headers = _get_headers()
    try:
        resp = req.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json={"filter": {"property": "Date", "date": {"equals": date_str}}},
        )
        for page in resp.json().get("results", []):
            req.patch(
                f"https://api.notion.com/v1/pages/{page['id']}",
                headers=headers,
                json={"archived": True},
            )
            logger.info("기존 페이지 아카이브: %s", page["id"])
    except Exception as e:
        logger.warning("기존 페이지 조회/삭제 오류: %s", e)


def _fmt_market(val: dict | None, is_rate: bool = False) -> str:
    """시장 지표 한 줄 포맷 — 종가(또는 환율)만 표시"""
    if not val:
        return "N/A"
    price = val.get("price")
    if price is None:
        return "N/A"
    if is_rate:
        return f"{price:,.2f}원"
    return f"{price:,.2f}"


def _build_blocks(
    summary: dict,
    domestic_themes: list[dict],
    international_themes: list[dict],
    market_data: dict,
) -> list[dict]:
    """노션 블록 리스트 생성"""
    blocks = []

    def heading(text: str, level: int = 2):
        tag = f"heading_{level}"
        return {"object": "block", "type": tag, tag: {"rich_text": [{"type": "text", "text": {"content": text}}]}}

    def paragraph(text: str):
        return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

    def bullet(text: str):
        return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

    def divider():
        return {"object": "block", "type": "divider", "divider": {}}

    # ── 오늘의 주요 지표 ─────────────────────────
    blocks.append(heading("📊 오늘의 주요 지표"))
    blocks.append(bullet(f"코스피 종가:   {_fmt_market(market_data.get('kospi'))}"))
    blocks.append(bullet(f"나스닥 종가:   {_fmt_market(market_data.get('nasdaq'))}"))
    blocks.append(bullet(f"원/달러 환율: {_fmt_market(market_data.get('usdkrw'), is_rate=True)}"))
    blocks.append(divider())

    # ── 주요 테마 (국내/해외 분리) ────────────────
    blocks.append(heading("🔥 주요 테마"))

    blocks.append(heading("국내", level=3))
    if domestic_themes:
        for t in sorted(domestic_themes, key=lambda x: -x.get("total_frequency", 0)):
            blocks.append(bullet(f"{t['theme_name']}  ({t.get('total_frequency', 0)}회 언급)"))
            if t.get("description"):
                blocks.append(paragraph(f"  → {t['description']}"))
    else:
        blocks.append(paragraph("  (테마 없음)"))

    blocks.append(heading("해외", level=3))
    if international_themes:
        for t in sorted(international_themes, key=lambda x: -x.get("total_frequency", 0)):
            blocks.append(bullet(f"{t['theme_name']}  ({t.get('total_frequency', 0)}회 언급)"))
            if t.get("description"):
                blocks.append(paragraph(f"  → {t['description']}"))
    else:
        blocks.append(paragraph("  (테마 없음)"))

    blocks.append(divider())

    # ── 뉴스 섹션 공통 헬퍼 ──────────────────────
    def append_news_section(news_list: list[dict]):
        for news in news_list:
            rank = news.get("rank", "?")
            title = news.get("title", "")
            blocks.append(heading(f"{rank}. {title}", level=3))
            blocks.append(paragraph(news.get("summary_kr", "")))
            blocks.append(paragraph(f"왜 중요한가: {news.get('why_important', '')}"))
            url = news.get("url", "")
            if url:
                blocks.append({"object": "block", "type": "paragraph", "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "원문 보기", "link": {"url": url}}}]
                }})

    # ── 국내 주요 뉴스 ────────────────────────────
    blocks.append(heading("📰 국내 주요 뉴스"))
    append_news_section(summary.get("domestic_news", []))
    blocks.append(divider())

    # ── 해외 주요 뉴스 ────────────────────────────
    blocks.append(heading("🌏 해외 주요 뉴스"))
    append_news_section(summary.get("international_news", []))
    blocks.append(divider())

    # ── 주요 섹터 ─────────────────────────────────
    if summary.get("key_sectors"):
        blocks.append(heading("🏭 주요 섹터"))
        for s in summary["key_sectors"]:
            blocks.append(bullet(s["sector"]))
            desc = s.get("description") or s.get("summary", "")
            if desc:
                blocks.append(paragraph(f"  → {desc}"))
        blocks.append(divider())

    # ── 주요 기업 ─────────────────────────────────
    if summary.get("key_companies"):
        blocks.append(heading("🏢 주요 기업"))
        for c in summary["key_companies"]:
            ticker = f" ({c['ticker']})" if c.get("ticker") else ""
            blocks.append(bullet(f"{c['company']}{ticker}"))
            desc = c.get("description") or c.get("note", "")
            if desc:
                blocks.append(paragraph(f"  → {desc}"))

    return blocks


def save_to_notion(
    summary: dict,
    domestic_themes: list[dict],
    international_themes: list[dict],
    market_data: dict,
    date_str: str | None = None,
) -> str | None:
    """노션에 페이지 생성. 성공 시 페이지 URL 반환."""
    if date_str is None:
        date_str = datetime.now(config.KST).strftime("%Y-%m-%d")

    _archive_existing(date_str)

    notion = _get_notion_client()
    database_id = os.environ["NOTION_DATABASE_ID"]

    properties = {
        "Title": {"title": [{"text": {"content": f"{date_str} 주식 뉴스 브리핑"}}]},
        "Date": {"date": {"start": date_str}},
    }

    blocks = _build_blocks(summary, domestic_themes, international_themes, market_data)

    try:
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=blocks[:100],
        )
        # Notion API는 한 번에 최대 100블록 — 초과분을 이어서 추가
        for i in range(100, len(blocks), 100):
            notion.blocks.children.append(page["id"], children=blocks[i:i + 100])
        url = page.get("url", "")
        logger.info("노션 저장 완료: %s", url)
        return url
    except Exception as e:
        logger.error("노션 저장 실패: %s", e)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sample_summary = {
        "domestic_news": [
            {"rank": 1, "title": "삼성전자 HBM 수출 증가", "summary_kr": "HBM 수출이 크게 늘었다.", "why_important": "반도체 업황 회복 신호다.", "url": "https://example.com/1"},
        ],
        "international_news": [
            {"rank": 1, "title": "Fed rate hold decision", "summary_kr": "연준이 금리를 동결했다.", "why_important": "금리 인하 기대가 커진다.", "url": "https://example.com/2"},
        ],
        "key_sectors": [{"sector": "반도체", "description": "AI 수요로 강세. HBM 중심 수출 확대."}],
        "key_companies": [{"company": "엔비디아", "ticker": "NVDA", "description": "AI GPU 수요 급증으로 실적 사상최고."}],
    }
    sample_dom_themes = [{"theme_name": "AI 반도체", "keywords": ["삼성", "HBM"], "total_frequency": 8, "description": "국내 반도체 수출 확대 흐름."}]
    sample_intl_themes = [{"theme_name": "미국 통화정책", "keywords": ["연준", "금리"], "total_frequency": 10, "description": "금리 동결로 위험자산 선호 확대."}]
    sample_market = {
        "kospi": {"price": 2541.23, "change": -12.34, "change_pct": -0.48},
        "nasdaq": {"price": 17842.56, "change": 125.34, "change_pct": 0.71},
        "usdkrw": {"price": 1381.50, "change": 3.20, "change_pct": 0.23},
    }
    url = save_to_notion(sample_summary, sample_dom_themes, sample_intl_themes, sample_market)
    if url:
        print(f"\n노션 페이지 생성 완료!\n{url}")
    else:
        print("\n저장 실패 — 환경변수(.env)와 노션 설정을 확인하세요.")
