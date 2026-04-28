# 이 파일은 뉴스 데이터 모델, 점수 계산, 파일 저장, 로그 작성 등의 도우미 함수입니다.

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    region: str
    score: int = 0


def select_top_news(news_items: List[NewsItem], region: str) -> List[NewsItem]:
    filtered = [item for item in news_items if item.region == region]
    sorted_items = sorted(filtered, key=lambda item: item.score, reverse=True)
    return sorted_items[:5]


def save_markdown_report(domestic: List[NewsItem], overseas: List[NewsItem]) -> str:
    now = datetime.now()
    date_text = now.strftime("%Y-%m-%d")
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{date_text}.md"

    lines = [f"📅 {now.year}년 {now.month}월 {now.day}일 아침 브리핑\n"]
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🇰🇷 국내 증시 요약")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    for idx, item in enumerate(domestic, 1):
        lines.append(f"[{idx}] {item.title}")
        lines.append(f"   - {item.summary}")
        lines.append(f"   - 원문 링크: {item.url}\n")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🌎 해외 증시 요약")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    for idx, item in enumerate(overseas, 1):
        lines.append(f"[{idx}] {item.title}")
        lines.append(f"   - {item.summary}")
        lines.append(f"   - 원문 링크: {item.url}\n")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💹 오늘의 주요 지표")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("- 코스피 종가: XXXX (전일대비 +X.X%)")
    lines.append("- 나스닥 종가: XXXX (전일대비 +X.X%)")
    lines.append("- 원/달러 환율: XXXX")
    lines.append("- 비트코인: XXXX")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return str(file_path)


def write_log(message: str):
    now = datetime.now()
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    file_path = logs_dir / f"{now.strftime('%Y-%m-%d')}.log"
    with file_path.open("a", encoding="utf-8") as f:
        f.write(f"{now.isoformat()} - {message}\n")
