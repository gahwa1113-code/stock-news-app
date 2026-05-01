"""
테마 클러스터링 — Claude API로 키워드를 의미 단위 테마로 묶기
실행 테스트: python -m analyzer.theme_clusterer
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


def cluster_themes_separate(
    dom_keyword_freq: dict,
    intl_keyword_freq: dict,
) -> tuple[list[dict], list[dict]]:
    """
    국내·해외 키워드를 한 번의 API 호출로 각각 테마 클러스터링.
    Returns: (domestic_themes, international_themes)
    """
    def fmt(freq: dict) -> str:
        if not freq:
            return "  (해당 키워드 없음)"
        top = sorted(freq.items(), key=lambda x: -x[1])[:30]
        return "\n".join(f"  - {kw} ({cnt}회)" for kw, cnt in top)

    prompt = f"""다음은 오늘 수집된 국내·해외 경제·증시 뉴스의 주요 키워드와 빈도입니다.
각 그룹의 키워드를 의미적으로 유사한 테마끼리 묶어주세요.

[국내 뉴스 키워드]
{fmt(dom_keyword_freq)}

[해외 뉴스 키워드]
{fmt(intl_keyword_freq)}

[규칙]
- 각 그룹(국내/해외)별로 테마는 최소 1개, 최대 5개
- theme_name은 한국어로 간결하게 (예: "미국 통화정책", "AI 반도체")
- description은 오늘 증시 동향 관점에서 이 테마의 핵심 내용을 1~2문장으로 설명
- 반드시 아래 JSON 형식으로만 응답 (설명 없이)

{{
  "domestic_themes": [
    {{
      "theme_name": "테마명",
      "keywords": ["키워드1", "키워드2"],
      "total_frequency": 합산빈도(정수),
      "description": "테마 설명 1~2문장"
    }}
  ],
  "international_themes": [
    {{
      "theme_name": "테마명",
      "keywords": ["키워드1", "키워드2"],
      "total_frequency": 합산빈도(정수),
      "description": "테마 설명 1~2문장"
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
            data = json.loads(raw)
            domestic = data.get("domestic_themes", [])
            international = data.get("international_themes", [])
            logger.info("국내 테마 %d개, 해외 테마 %d개 클러스터링 완료", len(domestic), len(international))
            return domestic, international
        except Exception as e:
            logger.warning("테마 분리 클러스터링 오류 (시도 %d/%d): %s", attempt + 1, config.LLM_MAX_RETRIES, e)
            if attempt < config.LLM_MAX_RETRIES - 1:
                time.sleep(config.LLM_BACKOFF_DELAYS[attempt])

    logger.error("테마 분리 클러스터링 최종 실패")
    return [], []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    dom_freq = {"삼성": 5, "반도체": 4, "HBM": 3, "금리": 2}
    intl_freq = {"연준": 8, "FOMC": 4, "엔비디아": 5, "AI": 4}
    dom, intl = cluster_themes_separate(dom_freq, intl_freq)
    print("\n--- 국내 테마 ---")
    for t in dom:
        print(f"  [{t['theme_name']}] {t['keywords']} (총 {t['total_frequency']}회)")
    print("\n--- 해외 테마 ---")
    for t in intl:
        print(f"  [{t['theme_name']}] {t['keywords']} (총 {t['total_frequency']}회)")
