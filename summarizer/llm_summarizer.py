"""
Gemini API로 Top 뉴스 요약 + 섹터/기업 한 번에 생성
실행 테스트: python -m summarizer.llm_summarizer
"""
import json
import logging
import re
import time

from openai import OpenAI

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from dotenv import load_dotenv
load_dotenv(override=True)

logger = logging.getLogger(__name__)
client = OpenAI(
    base_url=config.GEMINI_BASE_URL,
    api_key=os.environ["GEMINI_API_KEY"],
)


def generate_summary(
    top_articles: dict,
    domestic_themes: list[dict],
    international_themes: list[dict],
) -> dict:
    """
    top_articles: {"domestic": [...], "international": [...]}
    Returns: {
        "domestic_news": [...],
        "international_news": [...],
        "key_sectors": [...],
        "key_companies": [...]
    }
    """
    domestic = top_articles.get("domestic", [])
    international = top_articles.get("international", [])

    def format_articles(articles: list[dict], label: str) -> str:
        if not articles:
            return f"[{label}]\n  (해당 뉴스 없음)\n"
        text = f"[{label}]\n"
        for i, a in enumerate(articles, 1):
            text += (
                f"\n  [{i}위] 제목: {a.get('title', '')}\n"
                f"    요약: {a.get('summary', '(요약 없음)')}\n"
                f"    URL: {a.get('url', '')}\n"
            )
        return text

    def format_themes(themes: list[dict], label: str) -> str:
        if not themes:
            return f"[{label}]\n  (테마 없음)\n"
        text = f"[{label}]\n"
        for t in themes:
            text += f"  - {t['theme_name']} (언급 {t.get('total_frequency', 0)}회)\n"
        return text

    news_text = format_articles(domestic, "국내 뉴스") + "\n" + format_articles(international, "해외 뉴스")
    theme_text = format_themes(domestic_themes, "국내 주요 테마") + "\n" + format_themes(international_themes, "해외 주요 테마")

    prompt = f"""당신은 주식·경제 전문 애널리스트입니다.
아래 뉴스 정보를 바탕으로 한국어로 브리핑을 작성해주세요.

[오늘의 주요 테마]
{theme_text}

[뉴스 목록]
{news_text}

[작성 규칙]
- 모든 내용은 한국어로 작성
- 각 뉴스 summary_kr은 2~3문장 요약
- why_important는 투자자 관점에서 1문장
- domestic_news는 국내 뉴스 3개, international_news는 해외 뉴스 3개
- key_sectors: 뉴스에 등장한 주요 섹터, sector명과 description(동향 2문장) 포함
- key_companies: 뉴스에 등장한 주요 기업, company명·ticker·description(핵심 내용 1~2문장) 포함
- 반드시 아래 JSON 형식으로만 응답 (설명 없이)

{{
  "domestic_news": [
    {{
      "rank": 1,
      "title": "원제목",
      "summary_kr": "한국어 2~3문장 요약",
      "why_important": "왜 중요한지 1문장"
    }}
  ],
  "international_news": [
    {{
      "rank": 1,
      "title": "원제목",
      "summary_kr": "한국어 2~3문장 요약",
      "why_important": "왜 중요한지 1문장"
    }}
  ],
  "key_sectors": [
    {{
      "sector": "섹터명",
      "description": "섹터 동향 2문장"
    }}
  ],
  "key_companies": [
    {{
      "company": "기업명",
      "ticker": "티커 (모르면 빈 문자열)",
      "description": "핵심 내용 1~2문장"
    }}
  ]
}}"""

    for attempt in range(config.LLM_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=config.CLAUDE_MODEL,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            m = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
            if m:
                raw = m.group(1)
            else:
                m = re.search(r"\{[\s\S]*\}", raw)
                if m:
                    raw = m.group(0)
            result = json.loads(raw)
            # LLM이 URL을 변형할 수 있으므로 원본 URL을 순서대로 직접 주입
            for i, news in enumerate(result.get("domestic_news", [])):
                if i < len(domestic):
                    news["url"] = domestic[i].get("url", "")
            for i, news in enumerate(result.get("international_news", [])):
                if i < len(international):
                    news["url"] = international[i].get("url", "")
            logger.info("LLM 요약 생성 완료")
            return result
        except Exception as e:
            logger.warning("LLM 요약 오류 (시도 %d/%d): %s", attempt + 1, config.LLM_MAX_RETRIES, e)
            if attempt < config.LLM_MAX_RETRIES - 1:
                time.sleep(config.LLM_RETRY_DELAY_SEC * (attempt + 1))

    logger.error("LLM 요약 최종 실패 — 빈 결과 반환")
    return {"domestic_news": [], "international_news": [], "key_sectors": [], "key_companies": []}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sample_articles = {
        "domestic": [
            {"title": "삼성전자 HBM 수출 증가", "summary": "HBM 수출이 크게 늘었다.", "source": "네이버증권", "url": "https://example.com/1"},
        ],
        "international": [
            {"title": "Fed rate hold decision", "summary": "Fed가 금리를 동결했다.", "source": "Investing.com", "url": "https://example.com/2"},
            {"title": "NVIDIA record earnings", "summary": "AI 수요 급증.", "source": "Investing.com", "url": "https://example.com/3"},
        ],
    }
    sample_dom_themes = [{"theme_name": "AI 반도체", "keywords": ["삼성", "HBM"], "total_frequency": 8}]
    sample_intl_themes = [
        {"theme_name": "미국 통화정책", "keywords": ["연준", "금리"], "total_frequency": 10},
        {"theme_name": "AI 빅테크", "keywords": ["엔비디아", "AI"], "total_frequency": 8},
    ]
    result = generate_summary(sample_articles, sample_dom_themes, sample_intl_themes)
    print(json.dumps(result, ensure_ascii=False, indent=2))
