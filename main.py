# 뉴스 수집 → AI 요약 → Notion 저장까지 전체 파이프라인을 실행합니다
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
    write_log(f"마크다운 보고서 저장: {report_path}")

    try:
        notion = NotionClient()
        notion.save_briefing(top_domestic, top_overseas)
        write_log("Notion 브리핑 저장 완료")
    except Exception as error:
        write_log(f"Notion 저장 실패: {error}")
        print(f"주의: Notion 저장에 실패했습니다: {error}")


if __name__ == "__main__":
    main()
