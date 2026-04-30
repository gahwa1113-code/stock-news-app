import requests
import logging
from dataclasses import dataclass
from datetime import date
from src.config import DART_API_KEY

logger = logging.getLogger(__name__)

DART_BASE = "https://opendart.fss.or.kr/api"


@dataclass
class Disclosure:
    title: str
    url: str
    filed_at: str


def fetch_dart(stock_code: str, today: date) -> list[Disclosure]:
    today_str = today.strftime("%Y%m%d")
    try:
        res = requests.get(
            f"{DART_BASE}/list.json",
            params={
                "crtfc_key": DART_API_KEY,
                "stock_code": stock_code,
                "bgn_de": today_str,
                "end_de": today_str,
                "page_no": 1,
                "page_count": 40,
            },
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
        if data.get("status") != "000":
            return []

        results = []
        for item in data.get("list", []):
            rcept_no = item.get("rcept_no", "")
            results.append(Disclosure(
                title=item.get("report_nm", ""),
                url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
                filed_at=item.get("rcept_dt", ""),
            ))
        logger.info(f"[{stock_code}] DART 공시 {len(results)}건")
        return results
    except Exception as e:
        logger.error(f"DART 수집 실패 [{stock_code}]: {e}")
        return []
