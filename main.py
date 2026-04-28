# 이 파일은 앱 실행의 시작점입니다.
# 설정을 불러오고, 국내/해외 뉴스를 수집한 뒤 정리하고 저장합니다.

from config import settings
from news_sources.domestic import fetch_domestic_news
from news_sources.overseas import fetch_overseas_news
from notion_api import NotionClient
from utils import save_markdown_report, write_log, select_top_news


def main():
    write_log("앱 실행 시작")
    domestic_news = fetch_domestic_news()
    overseas_news = fetch_overseas_news()

    top_domestic = select_top_news(domestic_news, region="국내")
    top_overseas = select_top_news(overseas_news, region="해외")

    report_path = save_markdown_report(top_domestic, top_overseas)
    write_log(f"보고서 저장 완료: {report_path}")

    try:
        notion = NotionClient()
        notion.save_news_items(top_domestic + top_overseas)
        write_log("Notion 저장 완료")
    except Exception as error:
        write_log(f"Notion 저장 실패: {error}")
        print("주의: Notion 저장에 실패했습니다. .env 토큰이나 데이터베이스 ID를 확인하세요.")


if __name__ == "__main__":
    main()
