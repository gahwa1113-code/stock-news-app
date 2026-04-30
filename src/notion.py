import logging
import requests
from datetime import date

from src.config import (
    NOTION_API_KEY, NOTION_DB_STOCKS_ID, NOTION_DB_APPEARANCES_ID,
    GITHUB_RAW_BASE,
)
from src.filter import StockInfo
from src.news import NewsItem
from src.dart import Disclosure

logger = logging.getLogger(__name__)

_H = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def _chart_url(code: str, period: str, timestamp: str) -> str:
    return f"{GITHUB_RAW_BASE}/{code}_{period}.png?v={timestamp}"


def _fmt_market_cap(value: float) -> str:
    if value >= 10000:
        jo = int(value // 10000)
        eok = int(value % 10000)
        return f"{jo}조" if eok == 0 else f"{jo}조 {eok}억"
    return f"{int(value)}억"


def _find_stock_page(code: str) -> str | None:
    res = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB_STOCKS_ID}/query",
        headers=_H,
        json={"filter": {"property": "종목", "title": {"contains": f"({code})"}}},
        timeout=10,
    )
    res.raise_for_status()
    results = res.json().get("results", [])
    return results[0]["id"] if results else None


def _get_appearance_history(stock_page_id: str) -> list[dict]:
    """종목 페이지와 연결된 등장 이력을 날짜 오름차순으로 반환."""
    res = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB_APPEARANCES_ID}/query",
        headers=_H,
        json={
            "filter": {"property": "종목 ", "relation": {"contains": stock_page_id}},
            "sorts": [{"property": "날짜 ", "direction": "ascending"}],
        },
        timeout=15,
    )
    res.raise_for_status()
    entries = []
    for p in res.json().get("results", []):
        props = p["properties"]
        date_str = (props.get("날짜 ", {}).get("title") or [{}])[0].get("plain_text", "")
        change_rate = props.get("상승률 ", {}).get("number") or 0
        rt = props.get("상승 원인 ", {}).get("rich_text") or []
        reason = rt[0].get("plain_text", "") if rt else ""
        entries.append({"date": date_str, "change_rate": change_rate, "reason": reason})
    return entries


def find_or_create_master(stock: StockInfo, today: date) -> str:
    """종목 DB에서 page_id를 조회하고, 없으면 생성. 있으면 정보 갱신. page_id 반환."""
    page_id = _find_stock_page(stock.code)

    if page_id:
        existing = requests.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=_H, timeout=10,
        )
        existing.raise_for_status()
        current_count = existing.json()["properties"]["등장횟수"]["number"] or 0
        requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=_H,
            json={"properties": {
                "최근 등장일 ": {"date": {"start": today.isoformat()}},
                "등장횟수": {"number": current_count + 1},
                "시가총액 ": {"number": stock.market_cap},
            }},
            timeout=10,
        ).raise_for_status()
    else:
        res = requests.post(
            "https://api.notion.com/v1/pages",
            headers=_H,
            json={
                "parent": {"database_id": NOTION_DB_STOCKS_ID},
                "properties": {
                    "종목": {"title": [{"text": {"content": f"{stock.name} ({stock.code})"}}]},
                    "분석일 ": {"date": {"start": today.isoformat()}},
                    "최근 등장일 ": {"date": {"start": today.isoformat()}},
                    "등장횟수": {"number": 1},
                    "시가총액 ": {"number": stock.market_cap},
                },
            },
            timeout=10,
        )
        res.raise_for_status()
        page_id = res.json()["id"]

    return page_id


def update_stock_page_body(
    page_id: str,
    stock: StockInfo,
    timestamp: str,
) -> None:
    """종목 페이지 본문을 종목정보 + 등장이력 + 차트로 구성."""
    # 기존 블록 전체 삭제
    children = requests.get(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=_H, timeout=10,
    )
    children.raise_for_status()
    for block in children.json().get("results", []):
        requests.delete(
            f"https://api.notion.com/v1/blocks/{block['id']}",
            headers=_H, timeout=10,
        )

    # 등장 이력 조회
    history = _get_appearance_history(page_id)

    blocks = [
        # ── 종목 정보 ──────────────────────────────────────
        {
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "📊 종목 정보"}}]},
        },
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content":
                f"{stock.name} ({stock.code})　|　시가총액: {_fmt_market_cap(stock.market_cap)}"
            }}]},
        },
        {"type": "divider", "divider": {}},
        # ── 등장 이력 ──────────────────────────────────────
        {
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "📅 등장 이력"}}]},
        },
    ]

    for entry in history:
        rate_pct = entry["change_rate"] * 100
        sign = "+" if rate_pct >= 0 else ""
        label = f"{entry['date']}  |  {sign}{rate_pct:.1f}%  |  {entry['reason']}"
        blocks.append({
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": label}}]},
        })

    blocks += [
        {"type": "divider", "divider": {}},
        # ── 차트 ───────────────────────────────────────────
        {
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "📈 차트"}}]},
        },
        {
            "type": "image",
            "image": {"type": "external", "external": {"url": _chart_url(stock.code, "3M", timestamp)}},
        },
        {
            "type": "image",
            "image": {"type": "external", "external": {"url": _chart_url(stock.code, "1Y", timestamp)}},
        },
    ]

    requests.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=_H,
        json={"children": blocks},
        timeout=15,
    ).raise_for_status()


def add_appearance(
    stock: StockInfo,
    result: dict,
    related_url: str | None,
    today: date,
    stock_page_id: str | None,
) -> str:
    props = {
        "날짜 ": {"title": [{"text": {"content": today.isoformat()}}]},
        "상승률 ": {"number": stock.change_rate / 100},
        "시가 ": {"number": stock.open_price},
        "종가": {"number": stock.close},
        "거래대금_수치": {"number": stock.trading_amount},
        "변동폭": {"number": round(stock.volatility, 2) / 100},
        "상승 원인 ": {"rich_text": [{"text": {"content": result.get("reason", "")}}]},
    }
    if related_url:
        props["관련자료 "] = {"url": related_url}
    if stock_page_id:
        props["종목 "] = {"relation": [{"id": stock_page_id}]}

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_H,
        json={"parent": {"database_id": NOTION_DB_APPEARANCES_ID}, "properties": props},
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["id"]


def append_resources_to_page(
    page_id: str,
    disclosures: list[Disclosure],
    news: list[NewsItem],
) -> None:
    blocks = []

    if disclosures:
        blocks.append({
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "📋 DART 공시"}}]},
        })
        for d in disclosures:
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": d.title, "link": {"url": d.url}}}],
                },
            })

    if news:
        blocks.append({
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "📰 관련 뉴스"}}]},
        })
        for n in news[:10]:
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": f"{n.title} - {n.publisher}", "link": {"url": n.url}}}],
                },
            })

    if blocks:
        requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=_H,
            json={"children": blocks},
            timeout=15,
        ).raise_for_status()
