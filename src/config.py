import os
from dotenv import load_dotenv

load_dotenv()

DART_API_KEY = os.getenv("DART_API_KEY")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_STOCKS_ID = os.getenv("NOTION_DB_STOCKS_ID")
NOTION_DB_APPEARANCES_ID = os.getenv("NOTION_DB_APPEARANCES_ID")

GH_PAT = os.getenv("GH_PAT")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# 종목 필터 조건
MIN_SURGE_RATE = 15.0        # 전일 대비 상승률 (%)
MIN_TRADING_AMOUNT = 500     # 거래대금 (억 원)
MIN_VOLATILITY = 5.0         # 당일 변동폭 (%)
MIN_MARKET_CAP = 1000        # 시가총액 (억 원)

# GitHub raw 이미지 URL 베이스
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/charts"
