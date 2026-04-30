import logging
from dataclasses import dataclass
from datetime import date

import FinanceDataReader as fdr

from src.config import MIN_SURGE_RATE, MIN_TRADING_AMOUNT, MIN_VOLATILITY, MIN_MARKET_CAP

logger = logging.getLogger(__name__)


@dataclass
class StockInfo:
    code: str
    name: str
    open_price: float       # 당일 시가 (원)
    close: float
    change_rate: float      # 전일 대비 등락률 (%)
    trading_amount: float   # 거래대금 (억 원)
    volatility: float       # 당일 변동폭 (%)
    market_cap: float       # 시가총액 (억 원)


def _apply_filter(df) -> list[StockInfo]:
    df = df.copy()
    df = df[df['Volume'] > 0]
    df = df[df['Close'] > 0]
    df = df[df['Marcap'] / 1e8 >= MIN_MARKET_CAP]

    df = df[df['Code'].str.match(r'^\d{6}$')]  # 채권·ETN 등 비정규 코드 제외
    df['trading_amount'] = df['Amount'] / 1e8
    df['volatility'] = (df['High'] - df['Low']) / df['Close'] * 100

    surge_ok = df['ChagesRatio'] >= MIN_SURGE_RATE
    volume_ok = (
        (df['ChagesRatio'] >= 0) &
        (df['trading_amount'] >= MIN_TRADING_AMOUNT) &
        (df['volatility'] >= MIN_VOLATILITY)
    )
    df = df[surge_ok | volume_ok]

    return [
        StockInfo(
            code=str(row['Code']),
            name=str(row['Name']),
            open_price=float(row['Open']),
            close=float(row['Close']),
            change_rate=float(row['ChagesRatio']),
            trading_amount=float(row['trading_amount']),
            volatility=float(row['volatility']),
            market_cap=float(row['Marcap']) / 1e8,
        )
        for _, row in df.iterrows()
    ]


def filter_stocks(today: date | None = None) -> list[StockInfo]:
    if today is None:
        today = date.today()

    results = []
    for market in ('KOSPI', 'KOSDAQ'):
        try:
            df = fdr.StockListing(market)
            # KOSPI 거래량으로 휴장일 판단 (최초 1회만)
            if market == 'KOSPI' and int((df['Volume'] > 0).sum()) < 10:
                logger.info("오늘은 휴장일입니다.")
                return []
            results.extend(_apply_filter(df))
            logger.info(f"{market} 조회 완료")
        except Exception as e:
            logger.error(f"{market} 데이터 수집 실패: {e}")

    logger.info(f"조건 통과 종목: {len(results)}개")
    return results
