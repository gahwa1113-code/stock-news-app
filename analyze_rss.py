#!/usr/bin/env python3
import feedparser

print('=== RSS 분석 ===')
rss_urls = [
    ("Investing.com", "https://www.investing.com/rss/news.rss"),
    ("Google News 경제", "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=ko&gl=KR&ceid=KR:ko"),
]

for name, rss_url in rss_urls:
    print(f"=== {name} ===")
    try:
        feed = feedparser.parse(rss_url)
        print(f"피드 제목: {feed.feed.get('title', '제목 없음')}")
        print(f"엔트리 수: {len(feed.entries)}")

        if feed.entries:
            for i, entry in enumerate(feed.entries[:2]):
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")

                print(f"{i+1}. {title[:50]}...")
                print(f"   요약 존재: {len(summary) > 0}")
                print(f"   요약 길이: {len(summary)}")
                if summary:
                    print(f"   요약 내용: {summary[:100]}...")
                print(f"   링크: {link}")
        else:
            print("엔트리가 없습니다.")
    except Exception as e:
        print(f"RSS 오류: {e}")

    print()