import time
from config import settings
from utils import NewsItem


def fetch_domestic_news() -> list[NewsItem]:
    print("국내 뉴스: 테스트용 더미 데이터 사용")
    items = [
        NewsItem(
            title="코스피, 외국인 매수에 상승... 2,600선 회복",
            summary="코스피가 외국인 투자자의 매수세에 힘입어 2,600선을 회복했다.",
            url="https://news.naver.com/test1",
            source="네이버 경제",
            region="국내"
        ),
        NewsItem(
            title="원/달러 환율, 1,320원대 하락",
            summary="원/달러 환율이 달러 약세 영향으로 1,320원대까지 하락했다.",
            url="https://news.naver.com/test2",
            source="네이버 경제",
            region="국내"
        ),
        NewsItem(
            title="삼성전자, 2분기 실적 개선 전망",
            summary="삼성전자가 반도체 업황 회복으로 2분기 실적이 개선될 것으로 예상된다.",
            url="https://news.naver.com/test3",
            source="네이버 경제",
            region="국내"
        ),
        NewsItem(
            title="한국은행, 기준금리 동결 결정",
            summary="한국은행이 기준금리를 현 수준에서 동결하기로 결정했다.",
            url="https://news.naver.com/test4",
            source="네이버 경제",
            region="국내"
        ),
        NewsItem(
            title="코스닥, 중소형주 강세로 상승 마감",
            summary="코스닥 지수가 중소형 기술주 강세로 상승 마감했다.",
            url="https://news.naver.com/test5",
            source="네이버 경제",
            region="국내"
        ),
    ]
    time.sleep(settings["request_delay_seconds"])
    return items
