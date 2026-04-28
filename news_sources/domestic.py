# 이 파일은 Naver 경제 뉴스에서 국내 뉴스 제목과 링크를 수집합니다.

import time
import requests
import feedparser
from bs4 import BeautifulSoup
from config import settings
from utils import NewsItem, get_news_summary


def fetch_domestic_news() -> list[NewsItem]:
    # 일단 테스트를 위해 더미 데이터 사용
    print("국내 뉴스: 테스트용 더미 데이터 사용")
    items = [
        NewsItem(
            title="코스피, 외국인 매수에 상승... 2,600선 회복",
            summary="코스피가 외국인 투자자의 매수세에 힘입어 상승하며 2,600선을 회복했다. 기관 투자자도 동참하며 지수 상승을 이끌었다.",
            url="https://news.naver.com/test1",
            source="네이버 경제",
            region="국내"
        ),
        NewsItem(
            title="원/달러 환율, 1,320원대 하락",
            summary="원/달러 환율이 달러 약세 영향으로 1,320원대까지 하락했다. 위안화 강세도 환율 하락에 영향을 미쳤다.",
            url="https://news.naver.com/test2",
            source="네이버 경제",
            region="국내"
        )
    ]

    time.sleep(settings["request_delay_seconds"])
    return items
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")

        # 디버깅을 위해 페이지 내용 저장
        with open("naver_news_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        items = []

        # 간단한 방식: 모든 링크에서 뉴스 링크 필터링
        all_links = soup.select("a[href]")
        news_links = []

        for link_tag in all_links:
            href = link_tag.get("href")
            title = link_tag.get_text(strip=True)

            # 뉴스 링크 패턴 필터링
            if href and ('/main/read.naver' in href or '/article/' in href) and title and len(title) > 5:
                # 중복 제거
                if not any(existing['href'] == href for existing in news_links):
                    news_links.append({'tag': link_tag, 'href': href, 'title': title})

            if len(news_links) >= settings["news_per_region"] * 3:  # 충분히 많이 수집
                break

        print(f"총 {len(news_links)}개 뉴스 링크 발견")

        for i, news_link in enumerate(news_links[:settings["news_per_region"]]):
            link_tag = news_link['tag']
            title = news_link['title']
            link = news_link['href']

            print(f"링크 {i+1} 처리 중: {title[:30]}...")

            # 상대 URL 처리
            if link.startswith('/'):
                link = f"https://news.naver.com{link}"

            # 요약 정보 가져오기 시도
            summary = get_news_summary(link)

            items.append(NewsItem(
                title=title,
                summary=summary,
                url=link,
                source="Naver Finance",
                region="국내"
            ))

            print(f"  뉴스 추가 완료 (총 {len(items)}개)")

        print(f"국내 뉴스 {len(items)}개 수집 완료")
        time.sleep(settings["request_delay_seconds"])
        return items

    except Exception as e:
        print(f"국내 뉴스 수집 실패: {e}")
        return []
