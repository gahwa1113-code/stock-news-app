"""
전체 설정값 모음 — URL, 임계치, 키워드 사전 등
"""
import pytz

# ── 시간대 ────────────────────────────────────────
KST = pytz.timezone("Asia/Seoul")

# ── 크롤링 대상 URL ───────────────────────────────
NAVER_MAIN_URL = "https://finance.naver.com/news/mainnews.naver"
NAVER_LIST_URL = (
    "https://finance.naver.com/news/news_list.naver"
    "?mode=LSS2D&section_id=101&section_id2=258"
)
INVESTING_STOCK_URL = "https://www.investing.com/news/stock-market-news"
INVESTING_ECONOMY_URL = "https://www.investing.com/news/economy"

# ── 크롤링 설정 ───────────────────────────────────
REQUEST_DELAY_SEC = 1.5          # 요청 사이 대기 시간 (초)
NEWS_WINDOW_HOURS = 24           # 최근 N시간 이내 뉴스만 수집
MAX_ARTICLES_PER_SOURCE = 30     # 소스당 최대 수집 기사 수

# ── 분석 설정 ─────────────────────────────────────
MIN_KEYWORD_FREQ = 2             # 최소 등장 빈도 (이 이상만 유효 키워드)
TOP_DOMESTIC_COUNT = 3           # 국내 뉴스 상위 선정 수
TOP_INTERNATIONAL_COUNT = 3      # 해외 뉴스 상위 선정 수

# ── 중요도 점수 가중치 ─────────────────────────────
WEIGHT_THEME_FREQ = 3.0
SOURCE_WEIGHT = {
    "네이버증권": 1.0,
    "Investing.com": 1.2,
}
RECENCY_BONUS_HOURS = 1          # 기준시각 ±N시간 이내 기사에 보너스
RECENCY_BONUS_SCORE = 2.0

# ── 가산점 키워드 ──────────────────────────────────
HIGH_IMPORTANCE_KEYWORDS = [
    "급등", "급락", "쇼크", "사상최고", "사상최저",
    "Fed", "FOMC", "earnings", "guidance", "실적", "발표",
    "금리", "인상", "인하", "파산", "상장",
]

# ── 한국어 불용어 (키워드 추출 제외) ──────────────────
KOREAN_STOPWORDS = {
    "오늘", "어제", "내일", "기자", "뉴스", "투자자", "관련",
    "가운데", "이후", "이전", "최근", "올해", "지난", "현재",
    "경우", "시장", "주식", "증권", "전망", "분석", "예상",
    "기업", "회사", "국내", "해외", "글로벌", "국제",
}

# ── LLM 설정 ─────────────────────────────────────
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
CLAUDE_MODEL = "gemini-2.5-flash"
LLM_MAX_RETRIES = 3              # API 호출 실패 시 최대 재시도 횟수
LLM_RETRY_DELAY_SEC = 5         # 재시도 대기 시간 (초)

