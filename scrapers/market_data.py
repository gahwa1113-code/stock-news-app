"""
시장 지표 수집 — KOSPI, NASDAQ, 원/달러 환율
Yahoo Finance API 사용 (추가 패키지 불필요)
실행 테스트: python -m scrapers.market_data
"""
import logging
import requests

logger = logging.getLogger(__name__)

_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
_SYMBOLS = {"kospi": "^KS11", "nasdaq": "^IXIC", "usdkrw": "KRW=X"}


def _fetch(symbol: str) -> dict | None:
    try:
        resp = requests.get(_YAHOO_URL.format(symbol=symbol), headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        meta = resp.json()["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        prev = meta.get("previousClose") or meta.get("chartPreviousClose")
        if not price:
            return None
        change = round(price - prev, 2) if prev else None
        change_pct = round((price - prev) / prev * 100, 2) if prev else None
        return {"price": round(price, 2), "change": change, "change_pct": change_pct}
    except Exception as e:
        logger.warning("시장 데이터 수집 실패 (%s): %s", symbol, e)
        return None


def fetch_market_data() -> dict:
    """
    Returns: {
        "kospi":  {"price": float, "change": float, "change_pct": float},
        "nasdaq": {"price": float, "change": float, "change_pct": float},
        "usdkrw": {"price": float, "change": float, "change_pct": float},
    }
    None 값은 수집 실패를 의미
    """
    result = {key: _fetch(sym) for key, sym in _SYMBOLS.items()}
    logger.info(
        "시장 지표 수집 완료: KOSPI=%s, NASDAQ=%s, USD/KRW=%s",
        result["kospi"]["price"] if result["kospi"] else "N/A",
        result["nasdaq"]["price"] if result["nasdaq"] else "N/A",
        result["usdkrw"]["price"] if result["usdkrw"] else "N/A",
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    data = fetch_market_data()
    for key, val in data.items():
        if val:
            sign = "▲" if (val["change"] or 0) >= 0 else "▼"
            print(f"  {key.upper()}: {val['price']:,.2f}  {sign}{abs(val['change'] or 0):,.2f} ({val['change_pct']:+.2f}%)")
        else:
            print(f"  {key.upper()}: 수집 실패")
