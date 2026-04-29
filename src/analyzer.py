import json
import logging
import time
from google import genai
from google.genai import types
from datetime import date
from src.config import GEMINI_API_KEY
from src.news import NewsItem
from src.dart import Disclosure

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=GEMINI_API_KEY)

_MAX_RETRIES = 3
_RETRY_DELAY = 15  # 초

PROMPT = """다음은 {date} 한국 주식 종목 "{name}({code})"의 당일 뉴스/공시입니다.

[뉴스]
{news}

[DART 공시]
{disclosures}

이 종목의 당일 주가 상승({rate}%) 원인을 분석해 다음 JSON으로만 응답하세요:

{{
  "reason": "주가 상승 원인 1줄 요약 (50자 이내)"
}}
"""


def _format_news(news: list[NewsItem]) -> str:
    return "\n".join(f"- {n.title} ({n.publisher})" for n in news) or "없음"


def _format_disclosures(disclosures: list[Disclosure]) -> str:
    return "\n".join(f"- {d.title}" for d in disclosures) or "없음"


def gemini_analyze(
    stock_name: str,
    stock_code: str,
    change_rate: float,
    news: list[NewsItem],
    disclosures: list[Disclosure],
    today: date,
) -> dict:
    prompt = PROMPT.format(
        date=today.strftime("%Y-%m-%d"),
        name=stock_name,
        code=stock_code,
        news=_format_news(news),
        disclosures=_format_disclosures(disclosures),
        rate=f"{change_rate:.1f}",
    )

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            is_503 = "503" in str(e) or "UNAVAILABLE" in str(e)
            if is_503 and attempt < _MAX_RETRIES:
                logger.warning(f"Gemini 503 — {attempt}/{_MAX_RETRIES}회 시도, {_RETRY_DELAY}초 후 재시도 [{stock_code}]")
                time.sleep(_RETRY_DELAY)
            else:
                logger.error(f"Gemini 분석 실패 [{stock_code}]: {e}")
                return {"reason": "분석 실패", "themes": []}
