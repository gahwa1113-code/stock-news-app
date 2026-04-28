#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import get_news_summary

print('=== 요약 기능 테스트 ===')
test_urls = [
    'https://www.investing.com/news/stock-market-news/essilorluxottica-ceo-confident-in-share-price-recovery-over-time-4640860',
    'https://news.naver.com/main/read.naver?mode=LSD&mid=sec&sid1=101&oid=001&aid=0015000000'
]

for i, url in enumerate(test_urls):
    try:
        print(f'{i+1}. URL: {url[:60]}...')
        summary = get_news_summary(url)
        print(f'   요약: {summary[:150]}...')
        print()
    except Exception as e:
        print(f'   오류: {e}')
        print()