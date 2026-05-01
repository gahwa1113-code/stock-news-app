"""
DART 전자공시 크롤러 (Open DART API)
DART_API_KEY 환경변수 미설정 시 자동으로 건너뜀.
API 키 발급: https://opendart.fss.or.kr/uat/uia/easyLogin.do
실행 테스트: python -m scrapers.dart
"""
import logging
import os
import requests
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

DART_API_URL = "https://opendart.fss.or.kr/api/list.json"

# 주요 공시 유형만 수집 (사업보고서, 분기보고서, 주요사항보고서, 공정공시 등)
TARGET_REPORT_TYPES = {"A", "B", "C", "D"}


def fetch_dart_disclosures() -> list[dict]:
    """Open DART API로 오늘의 주요 공시 수집. API 키 없으면 빈 리스트 반환."""
    api_key = os.environ.get("DART_API_KEY", "")
    if not api_key:
        logger.info("DART_API_KEY 미설정 — DART 공시 수집 건너뜀")
        return []

    today = datetime.now(config.KST).strftime("%Y%m%d")
    yesterday = (datetime.now(config.KST) - timedelta(days=1)).strftime("%Y%m%d")

    articles = []
    try:
        params = {
            "crtfc_key": api_key,
            "bgn_de": yesterday,
            "end_de": today,
            "page_count": config.MAX_ARTICLES_PER_SOURCE,
            "sort": "date",
            "sort_mth": "desc",
        }
        resp = requests.get(DART_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "000":
            logger.warning("DART API 오류: %s", data.get("message", ""))
            return []

        for item in data.get("list", []):
            rcept_no = item.get("rcept_no", "")
            corp_name = item.get("corp_name", "")
            report_name = item.get("report_nm", "")
            rcept_dt = item.get("rcept_dt", "")
            pblntf_ty = item.get("pblntf_ty", "")

            if pblntf_ty not in TARGET_REPORT_TYPES:
                continue

            url = (
                f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
                if rcept_no else ""
            )

            published_at = None
            if rcept_dt and len(rcept_dt) == 8:
                try:
                    dt = datetime.strptime(rcept_dt, "%Y%m%d")
                    published_at = config.KST.localize(dt)
                except Exception:
                    pass

            articles.append({
                "title": f"[공시] {corp_name} — {report_name}",
                "summary": f"{corp_name}이(가) '{report_name}' 공시를 제출했습니다.",
                "url": url,
                "source": "DART",
                "published_at": published_at,
                "category": pblntf_ty,
            })

            if len(articles) >= config.MAX_ARTICLES_PER_SOURCE:
                break

    except Exception as e:
        logger.warning("DART 공시 수집 오류: %s", e)

    logger.info("DART: %d개 공시 수집", len(articles))
    return articles


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = fetch_dart_disclosures()
    print(f"\n총 {len(results)}개 공시 수집됨\n")
    for i, a in enumerate(results[:5], 1):
        print(f"{i}. {a['title']}")
        print(f"   시각: {a['published_at']}")
        print(f"   URL: {a['url']}\n")
