#!/usr/bin/env python3
import feedparser

# RSS 테스트
rss_urls = [
    "https://www.yna.co.kr/rss/economy.xml",  # 연합뉴스 경제
    "https://www.hankyung.com/rss/01",  # 한국경제
]

for rss_url in rss_urls:
    try:
        print(f"RSS URL 테스트: {rss_url}")
        feed = feedparser.parse(rss_url)

        print(f"피드 제목: {feed.feed.get('title', '제목 없음')}")
        print(f"엔트리 수: {len(feed.entries)}")

        if feed.entries:
            for i, entry in enumerate(feed.entries[:3]):
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                print(f"{i+1}. {title[:50]}...")
                print(f"   링크: {link}")
                print(f"   요약 길이: {len(summary)}")
                print()
            break
        else:
            print("엔트리가 없습니다.")
            print()

    except Exception as e:
        print(f"RSS 오류: {e}")
        print()