import logging
import time
from datetime import date

from src.filter import filter_stocks
from src.chart import generate_charts
from src.news import fetch_naver_news
from src.dart import fetch_dart
from src.analyzer import gemini_analyze
from src.github_uploader import upload_chart
from src.notion import (
    find_or_create_master,
    update_stock_page_body,
    add_appearance,
    append_resources_to_page,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    today = date.today()
    stocks = filter_stocks(today)

    if not stocks:
        logger.info("조건 통과 종목 없음 (휴장일 포함) — 종료")
        return

    logger.info(f"=== {today} 분석 시작: {len(stocks)}개 종목 ===")
    timestamp = today.strftime("%Y%m%d")

    for stock in stocks:
        try:
            logger.info(f"처리 시작: {stock.name} ({stock.code})")

            path_3m, path_1y = generate_charts(stock.code, stock.name, today)
            upload_chart(path_3m, stock.code, "3M")
            upload_chart(path_1y, stock.code, "1Y")

            news = fetch_naver_news(stock.name, today, top_n=10)
            disclosures = fetch_dart(stock.code, today)

            related_url = (
                disclosures[0].url if disclosures
                else (news[0].url if news else None)
            )

            result = gemini_analyze(
                stock.name, stock.code, stock.change_rate,
                news, disclosures, today,
            )

            stock_page_id = find_or_create_master(stock, today=today)
            time.sleep(0.4)

            page_id = add_appearance(stock, result, related_url, today, stock_page_id)
            time.sleep(0.4)

            append_resources_to_page(page_id, disclosures, news)
            time.sleep(0.4)

            update_stock_page_body(stock_page_id, stock, timestamp)
            time.sleep(0.4)

            logger.info(f"완료: {stock.name} ({stock.code})")

        except Exception as e:
            logger.error(f"[{stock.code}] 처리 중 오류 — 다음 종목 계속: {e}")

    logger.info("=== 전체 완료 ===")


if __name__ == "__main__":
    main()
