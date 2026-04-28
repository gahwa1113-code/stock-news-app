import requests
from bs4 import BeautifulSoup

url = "https://news.naver.com/section/101"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

response = requests.get(url, headers=headers, timeout=10)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, "html.parser")

# HTML 파일 저장
with open("naver_news_debug.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("네이버 뉴스 페이지 HTML 저장 완료")
print(f"페이지 제목: {soup.title.text if soup.title else '제목 없음'}")

# 새로운 방식: 모든 링크에서 뉴스 링크 필터링
all_links = soup.select("a[href]")
news_links = []

for link_tag in all_links:
    href = link_tag.get("href")
    title = link_tag.get_text(strip=True)

    # 뉴스 링크 패턴 필터링
    if href and ('/main/read.naver' in href or '/article/' in href) and title and len(title) > 5:
        # 중복 제거
        if not any(existing['href'] == href for existing in news_links):
            news_links.append({'href': href, 'title': title})

    if len(news_links) >= 20:  # 충분히 많이 수집
        break

print(f"총 {len(news_links)}개 뉴스 링크 발견")

for i, news in enumerate(news_links[:5]):
    print(f"{i+1}. {news['title'][:50]}...")
    print(f"   URL: {news['href']}")
    print()