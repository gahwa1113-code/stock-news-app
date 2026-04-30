"""
Investing.com 뉴스 크롤러 (playwright 사용 — JS 렌더링 대응)
실행 테스트: python -m scrapers.investing_com
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def _is_recent(dt: datetime | None) -> bool:
    if dt is None:
        return False
    now = datetime.now(config.KST)
    cutoff = now - timedelta(hours=config.NEWS_WINDOW_HOURS)
    if dt.tzinfo is None:
        dt = config.KST.localize(dt)
    return dt >= cutoff


async def _fetch_with_playwright(url: str) -> list[dict]:
    """playwright로 JS 렌더링 후 기사 목록 추출"""
    from playwright.async_api import async_playwright

    articles = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(2000)

            # Investing.com 기사 카드 선택자
            cards = await page.query_selector_all("article, [data-test='article-item']")
            if not cards:
                cards = await page.query_selector_all(".articleItem, .js-article-item")

            for card in cards[: config.MAX_ARTICLES_PER_SOURCE]:
                try:
                    title_el = await card.query_selector("a[href], h3 a, .title a")
                    if not title_el:
                        continue
                    title = await title_el.inner_text()
                    href = await title_el.get_attribute("href")
                    article_url = (
                        href if href and href.startswith("http")
                        else "https://www.investing.com" + (href or "")
                    )

                    time_el = await card.query_selector("time, [data-test='article-publish-date']")
                    published_at = None
                    if time_el:
                        dt_attr = await time_el.get_attribute("datetime")
                        if dt_attr:
                            try:
                                published_at = datetime.fromisoformat(dt_attr.replace("Z", "+00:00"))
                                published_at = published_at.astimezone(config.KST)
                            except Exception:
                                pass

                    if not _is_recent(published_at):
                        continue

                    articles.append({
                        "title": title.strip(),
                        "summary": "",
                        "url": article_url,
                        "source": "Investing.com",
                        "published_at": published_at,
                        "category": "",
                    })
                except Exception as e:
                    logger.debug("카드 파싱 오류: %s", e)

        except Exception as e:
            logger.warning("Investing.com 크롤링 오류 (%s): %s", url, e)
        finally:
            await browser.close()

    return articles


def fetch_investing_news() -> list[dict]:
    """Investing.com 뉴스 수집 (동기 래퍼)"""
    urls = [config.INVESTING_STOCK_URL, config.INVESTING_ECONOMY_URL]
    all_articles = []

    for url in urls:
        articles = asyncio.run(_fetch_with_playwright(url))
        all_articles.extend(articles)
        time.sleep(config.REQUEST_DELAY_SEC)

    # 중복 URL 제거
    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    logger.info("Investing.com: %d개 기사 수집", len(unique))
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = fetch_investing_news()
    print(f"\n총 {len(results)}개 기사 수집됨\n")
    for i, a in enumerate(results[:5], 1):
        print(f"{i}. {a['title']}")
        print(f"   출처: {a['source']} | 시각: {a['published_at']}")
        print(f"   URL: {a['url']}\n")
