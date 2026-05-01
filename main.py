"""
주식 뉴스 봇 — 전체 파이프라인 진입점
실행: python main.py
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(override=True)

import config

# Windows 터미널 UTF-8 출력 설정
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from scrapers.naver_finance import fetch_naver_news
from scrapers.hankyung import fetch_hankyung_news
from scrapers.mk import fetch_mk_news
from scrapers.dart import fetch_dart_disclosures
from scrapers.investing_com import fetch_investing_news
from scrapers.bloomberg import fetch_bloomberg_news
from scrapers.market_data import fetch_market_data
from analyzer.keyword_extractor import extract_keywords
from analyzer.theme_clusterer import cluster_themes_separate
from analyzer.importance_scorer import score_articles
from summarizer.llm_summarizer import generate_summary
from storage.notion_writer import save_to_notion

# ── 로그 설정 ─────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
date_str = datetime.now(config.KST).strftime("%Y-%m-%d")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/{date_str}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("main")


def run():
    logger.info("=" * 50)
    logger.info("주식 뉴스 봇 시작: %s", datetime.now(config.KST).strftime("%Y-%m-%d %H:%M KST"))
    logger.info("=" * 50)

    # ── 1단계: 뉴스 수집 + 시장 지표 ──────────────
    logger.info("[1단계] 뉴스 크롤링 및 시장 지표 수집 시작")
    articles = []

    try:
        naver_articles = fetch_naver_news()
        articles.extend(naver_articles)
        logger.info("  네이버 증권: %d개", len(naver_articles))
    except Exception as e:
        logger.error("  네이버 크롤링 실패: %s", e)

    try:
        hankyung_articles = fetch_hankyung_news()
        articles.extend(hankyung_articles)
        logger.info("  한국경제: %d개", len(hankyung_articles))
    except Exception as e:
        logger.error("  한국경제 크롤링 실패: %s", e)

    try:
        mk_articles = fetch_mk_news()
        articles.extend(mk_articles)
        logger.info("  매일경제: %d개", len(mk_articles))
    except Exception as e:
        logger.error("  매일경제 크롤링 실패: %s", e)

    try:
        dart_articles = fetch_dart_disclosures()
        articles.extend(dart_articles)
        logger.info("  DART 공시: %d개", len(dart_articles))
    except Exception as e:
        logger.error("  DART 크롤링 실패: %s", e)

    try:
        investing_articles = fetch_investing_news()
        articles.extend(investing_articles)
        logger.info("  Investing.com: %d개", len(investing_articles))
    except Exception as e:
        logger.error("  Investing.com 크롤링 실패: %s", e)

    try:
        bloomberg_articles = fetch_bloomberg_news()
        articles.extend(bloomberg_articles)
        logger.info("  Bloomberg: %d개", len(bloomberg_articles))
    except Exception as e:
        logger.error("  Bloomberg 크롤링 실패: %s", e)

    if not articles:
        logger.error("수집된 기사가 없습니다. 종료합니다.")
        sys.exit(1)

    logger.info("  총 수집: %d개", len(articles))

    try:
        market_data = fetch_market_data()
    except Exception as e:
        logger.error("  시장 지표 수집 실패: %s", e)
        market_data = {}

    # ── 2단계: 키워드 추출 ────────────────────────
    logger.info("[2단계] 키워드 추출 시작")
    keyword_freq, keyword_to_ids = extract_keywords(articles)

    # 국내/해외 테마 분리를 위한 별도 키워드 추출
    domestic_articles = [a for a in articles if a.get("source") in config.DOMESTIC_SOURCES]
    international_articles = [a for a in articles if a.get("source") not in config.DOMESTIC_SOURCES]
    dom_kw_freq, _ = extract_keywords(domestic_articles, min_freq=1)
    intl_kw_freq, _ = extract_keywords(international_articles, min_freq=1)

    # ── 3단계: 테마 클러스터링 ────────────────────
    logger.info("[3단계] 테마 클러스터링 시작")
    domestic_themes, international_themes = cluster_themes_separate(dom_kw_freq, intl_kw_freq)
    themes = domestic_themes + international_themes

    # ── 4단계: 중요도 점수 → Top 선정 ─────────────
    logger.info("[4단계] 중요도 점수 산정 시작")
    top_articles = score_articles(articles, keyword_freq, keyword_to_ids, themes)
    logger.info("  국내 %d개, 해외 %d개 선정", len(top_articles["domestic"]), len(top_articles["international"]))

    # ── 5단계: LLM 요약 생성 ─────────────────────
    logger.info("[5단계] LLM 요약 생성 시작")
    summary = generate_summary(top_articles, domestic_themes, international_themes)

    # ── 6단계: Notion 저장 ───────────────────────
    logger.info("[6단계] Notion 저장 시작")
    notion_url = save_to_notion(summary, domestic_themes, international_themes, market_data, date_str)

    # ── 로컬 JSON 백업 ───────────────────────────
    backup_path = f"logs/{date_str}_backup.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "date": date_str,
                "market_data": market_data,
                "domestic_themes": domestic_themes,
                "international_themes": international_themes,
                "summary": summary,
            },
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    logger.info("JSON 백업 저장: %s", backup_path)

    logger.info("=" * 50)
    if notion_url:
        logger.info("완료! 노션 페이지: %s", notion_url)
    else:
        logger.error("노션 저장 실패 — JSON 백업만 있음: %s", backup_path)
        logger.info("=" * 50)
        sys.exit(1)
    logger.info("=" * 50)


if __name__ == "__main__":
    run()
