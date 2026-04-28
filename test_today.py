#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date
print(f'=== 오늘 날짜 뉴스 테스트: {date.today()} ===')
print()

from news_sources.domestic import fetch_domestic_news

print('국내 뉴스 수집 테스트...')
domestic_news = fetch_domestic_news()
print(f'\n국내 뉴스 {len(domestic_news)}개 수집 완료')

if domestic_news:
    print('\n=== 국내 뉴스 샘플 ===')
    for i, news in enumerate(domestic_news[:3]):
        print(f'{i+1}. {news.title[:50]}...')
        summary_text = news.summary[:100] if news.summary else "요약 없음"
        print(f'   요약: {summary_text}...')
        print(f'   출처: {news.source}')
        print(f'   URL: {news.url}')
        print()
else:
    print('국내 뉴스가 수집되지 않았습니다.')