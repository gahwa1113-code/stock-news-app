"""
중요도 점수 산정 → 상위 N개 뉴스 선정
실행 테스트: python -m analyzer.importance_scorer
"""
import logging
import re
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

DEDUP_THRESHOLD = 0.45  # 제목 단어 Jaccard 유사도 이 이상이면 중복으로 간주


def _title_words(title: str) -> set[str]:
    return set(re.findall(r"\w+", title.lower()))


def _pick_unique(articles: list[dict], n: int) -> list[dict]:
    """점수 순 정렬된 기사에서 제목이 유사한 중복을 제거하고 상위 n개 반환."""
    kept: list[dict] = []
    for article in articles:
        words = _title_words(article.get("title", ""))
        duplicate = False
        for k in kept:
            k_words = _title_words(k.get("title", ""))
            union = k_words | words
            if union and len(k_words & words) / len(union) >= DEDUP_THRESHOLD:
                duplicate = True
                break
        if not duplicate:
            kept.append(article)
        if len(kept) == n:
            break
    return kept


def score_articles(
    articles: list[dict],
    keyword_freq: dict,
    keyword_to_ids: dict,
    themes: list[dict],
) -> dict:
    """
    각 기사에 중요도 점수를 매겨 국내/해외 상위 뉴스를 반환.
    Returns: {"domestic": [...], "international": [...]}
    """
    # 키워드 → 테마 빈도 매핑
    keyword_theme_freq: dict[str, float] = {}
    for theme in themes:
        for kw in theme.get("keywords", []):
            keyword_theme_freq[kw] = theme.get("total_frequency", 0)

    now = datetime.now(config.KST)
    recency_cutoff = now - timedelta(hours=config.RECENCY_BONUS_HOURS)

    scored = []
    for idx, article in enumerate(articles):
        score = 0.0
        text = f"{article.get('title', '')} {article.get('summary', '')}"

        # 1) 테마 빈도 점수
        for kw, ids in keyword_to_ids.items():
            if idx in ids:
                score += keyword_theme_freq.get(kw, keyword_freq.get(kw, 0)) * config.WEIGHT_THEME_FREQ

        # 2) 출처 가중치
        score += config.SOURCE_WEIGHT.get(article.get("source", ""), 1.0)

        # 3) 최신도 점수
        pub = article.get("published_at")
        if pub:
            if pub.tzinfo is None:
                pub = config.KST.localize(pub)
            if pub >= recency_cutoff:
                score += config.RECENCY_BONUS_SCORE

        # 4) 핵심 키워드 가산점
        for kw in config.HIGH_IMPORTANCE_KEYWORDS:
            if kw.lower() in text.lower():
                score += 1.0

        scored.append({**article, "score": round(score, 2)})

    scored.sort(key=lambda x: x["score"], reverse=True)

    domestic = [a for a in scored if a.get("source") == "네이버증권"]
    international = [a for a in scored if a.get("source") != "네이버증권"]

    top_domestic = _pick_unique(domestic, config.TOP_DOMESTIC_COUNT)
    top_international = _pick_unique(international, config.TOP_INTERNATIONAL_COUNT)

    logger.info("국내 상위 %d개, 해외 상위 %d개 뉴스 선정", len(top_domestic), len(top_international))
    return {"domestic": top_domestic, "international": top_international}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from datetime import timezone
    now = datetime.now(config.KST)
    sample_articles = [
        {"title": "연준 금리 동결, 시장 급등", "summary": "Fed 금리 동결 결정.", "source": "네이버증권", "published_at": now - timedelta(minutes=30)},
        {"title": "엔비디아 실적 사상최고", "summary": "AI 반도체 수요 급증.", "source": "Investing.com", "published_at": now - timedelta(hours=2)},
        {"title": "삼성전자 반도체 수출 증가", "summary": "반도체 호실적.", "source": "네이버증권", "published_at": now - timedelta(hours=5)},
        {"title": "테슬라 가이던스 쇼크", "summary": "guidance 하향.", "source": "Investing.com", "published_at": now - timedelta(hours=1)},
        {"title": "국내 증시 전망", "summary": "전반적 상승 기대.", "source": "네이버증권", "published_at": now - timedelta(hours=10)},
        {"title": "금리 인하 기대감 확산", "summary": "금리 인하 전망.", "source": "네이버증권", "published_at": now - timedelta(minutes=45)},
    ]
    sample_freq = {"연준": 4, "금리": 5, "엔비디아": 3, "반도체": 3}
    sample_mapping = {"연준": [0], "금리": [0, 5], "엔비디아": [1], "반도체": [1, 2]}
    sample_themes = [
        {"theme_name": "통화정책", "keywords": ["연준", "금리"], "total_frequency": 9},
        {"theme_name": "AI반도체", "keywords": ["엔비디아", "반도체"], "total_frequency": 6},
    ]
    top5 = score_articles(sample_articles, sample_freq, sample_mapping, sample_themes)
    print("\n--- 상위 뉴스 ---")
    for i, a in enumerate(top5, 1):
        print(f"{i}. [{a['score']}점] {a['title']}")
