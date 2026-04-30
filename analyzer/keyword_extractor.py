"""
키워드 추출기 — 한국어(kiwipiepy) + 영어 명사 추출 후 빈도 집계
실행 테스트: python -m analyzer.keyword_extractor
"""
import logging
import re
from collections import Counter, defaultdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

# kiwipiepy — Windows에서 프로젝트 경로에 한글이 포함된 경우 C 확장이 모델을 못 찾는 문제를 우회.
# ASCII 경로로 복사해둔 모델을 사용하고, Linux(GitHub Actions)에서는 기본 경로 사용.
import sys as _sys
_KIWI_MODEL_PATH = (
    r"C:\Users\82104\AppData\Local\kiwipiepy_model"
    if _sys.platform == "win32" else None
)
_kiwi = None

def _get_kiwi():
    global _kiwi
    if _kiwi is not None:
        return _kiwi
    try:
        from kiwipiepy import Kiwi
        _kiwi = Kiwi(model_path=_KIWI_MODEL_PATH) if _KIWI_MODEL_PATH else Kiwi()
        logger.info("kiwipiepy 초기화 완료")
    except Exception as e:
        logger.warning("kiwipiepy 초기화 실패 (%s) — 한국어 키워드 추출 건너뜀", e)
        _kiwi = False
    return _kiwi

# 영어 → 한국어 정규화 사전
EN_TO_KR = {
    "federal reserve": "연준",
    "fed": "연준",
    "fomc": "FOMC",
    "rate": "금리",
    "interest rate": "금리",
    "inflation": "인플레이션",
    "nvidia": "엔비디아",
    "samsung": "삼성",
    "apple": "애플",
    "tesla": "테슬라",
    "earnings": "실적",
    "gdp": "GDP",
    "recession": "경기침체",
    "semiconductor": "반도체",
    "ai": "AI",
}


def _extract_korean_nouns(text: str) -> list[str]:
    kiwi = _get_kiwi()
    if not kiwi:
        return []
    try:
        tokens = kiwi.tokenize(text)
        return [t.form for t in tokens if t.tag.startswith("NN") and len(t.form) >= 2]
    except Exception as e:
        logger.warning("kiwipiepy 토크나이징 오류: %s", e)
        return []


def _extract_english_nouns(text: str) -> list[str]:
    text_lower = text.lower()
    nouns = []
    for en, kr in EN_TO_KR.items():
        if en in text_lower:
            nouns.append(kr)
    # 단순 영대문자 단어 (티커, 약어)
    for word in re.findall(r"\b[A-Z]{2,6}\b", text):
        nouns.append(word)
    return nouns


def extract_keywords(articles: list[dict], min_freq: int | None = None) -> tuple[dict, dict]:
    """
    Returns:
        keyword_freq: {keyword: count}
        keyword_to_ids: {keyword: [article_index, ...]}
    min_freq: 최소 빈도 override (None이면 config.MIN_KEYWORD_FREQ 사용)
    """
    freq: Counter = Counter()
    keyword_to_ids: defaultdict = defaultdict(list)

    for idx, article in enumerate(articles):
        text = f"{article.get('title', '')} {article.get('summary', '')}"

        nouns = _extract_korean_nouns(text) + _extract_english_nouns(text)
        nouns = [n for n in nouns if n not in config.KOREAN_STOPWORDS]

        for noun in nouns:
            freq[noun] += 1
            if idx not in keyword_to_ids[noun]:
                keyword_to_ids[noun].append(idx)

    # 최소 빈도 필터
    threshold = min_freq if min_freq is not None else config.MIN_KEYWORD_FREQ
    valid = {k: v for k, v in freq.items() if v >= threshold}
    keyword_to_ids = {k: keyword_to_ids[k] for k in valid}

    logger.info("유효 키워드 %d개 추출", len(valid))
    return valid, keyword_to_ids


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sample = [
        {"title": "연준 금리 동결 결정, 시장 안도", "summary": "Fed가 금리를 동결했다."},
        {"title": "엔비디아 AI 반도체 수요 급증", "summary": "엔비디아 실적 사상최고."},
        {"title": "삼성전자 반도체 수출 증가", "summary": "삼성 반도체 호실적."},
        {"title": "금리 인하 기대감에 나스닥 급등", "summary": "금리 인하 기대로 주가 상승."},
    ]
    freq, mapping = extract_keywords(sample)
    print("\n--- 키워드 빈도 ---")
    for kw, cnt in sorted(freq.items(), key=lambda x: -x[1]):
        print(f"  {kw}: {cnt}회")
