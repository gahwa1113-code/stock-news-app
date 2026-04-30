"""
Notion 출력 포맷 테스트 — 실제 스크래핑/LLM 없이 샘플 데이터로 저장
실행: python test_notion.py
"""
import logging
import sys
from dotenv import load_dotenv
load_dotenv(override=True)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from storage.notion_writer import save_to_notion

sample_domestic_themes = [
    {
        "theme_name": "AI 반도체",
        "keywords": ["삼성", "HBM", "엔비디아", "반도체"],
        "total_frequency": 14,
        "description": "HBM 수출 호조와 엔비디아 협력 확대로 국내 반도체 기업들의 실적 기대감이 높아지고 있다. AI 인프라 투자 확대가 수요를 견인하는 중이다.",
    },
    {
        "theme_name": "금리·통화정책",
        "keywords": ["금리", "한국은행", "기준금리"],
        "total_frequency": 9,
        "description": "한국은행이 연내 추가 금리 인하 가능성을 시사하며 부동산·소비 심리 개선에 대한 기대가 형성됐다.",
    },
    {
        "theme_name": "2차전지",
        "keywords": ["LG에너지솔루션", "배터리", "전기차"],
        "total_frequency": 7,
        "description": "전기차 수요 둔화 우려에도 불구하고 유럽 보조금 정책 재편 소식에 2차전지 섹터 관심이 되살아나고 있다.",
    },
]

sample_international_themes = [
    {
        "theme_name": "미국 통화정책",
        "keywords": ["연준", "FOMC", "금리인하"],
        "total_frequency": 18,
        "description": "연준이 금리 동결을 유지하면서도 연내 인하 여지를 열어둬 글로벌 위험자산 선호 심리가 회복됐다.",
    },
    {
        "theme_name": "빅테크 실적",
        "keywords": ["엔비디아", "애플", "마이크로소프트", "AI"],
        "total_frequency": 13,
        "description": "AI 수요 급증으로 엔비디아·마이크로소프트 등 빅테크 실적이 시장 예상을 크게 웃돌며 나스닥을 견인했다.",
    },
    {
        "theme_name": "미·중 무역갈등",
        "keywords": ["관세", "중국", "무역"],
        "total_frequency": 8,
        "description": "미국의 중국산 반도체 장비 수출 규제 강화 소식이 글로벌 공급망 불확실성을 다시 키우고 있다.",
    },
]

sample_summary = {
    "domestic_news": [
        {
            "rank": 1,
            "title": "삼성전자, 엔비디아에 HBM3E 공급 최종 승인",
            "summary_kr": "삼성전자가 엔비디아의 HBM3E 품질 테스트를 최종 통과해 공급 계약이 확정됐다. 이번 계약으로 삼성전자는 SK하이닉스에 빼앗긴 HBM 시장 점유율 일부를 되찾을 것으로 기대된다. 하반기 공급 물량은 전체 엔비디아 HBM 수요의 약 20% 수준으로 전해진다.",
            "why_important": "HBM 시장 재진입 성공은 삼성전자 반도체 부문 실적 반등의 핵심 변수로, 주가 재평가 계기가 될 수 있다.",
            "url": "https://finance.naver.com/news/sample1",
        },
        {
            "rank": 2,
            "title": "한국은행, 연내 기준금리 추가 인하 시사",
            "summary_kr": "이창용 한국은행 총재가 물가 안정 흐름이 지속될 경우 연내 추가 금리 인하를 검토할 수 있다고 밝혔다. 시장에서는 3분기 중 25bp 인하를 기정사실로 받아들이는 분위기다. 이에 따라 국내 채권 금리가 하락하고 성장주 중심의 매수세가 유입됐다.",
            "why_important": "금리 인하 기대는 고PER 성장주·리츠·배당주에 유리한 환경을 조성해 코스피 상승 동력으로 작용할 수 있다.",
            "url": "https://finance.naver.com/news/sample2",
        },
        {
            "rank": 3,
            "title": "LG에너지솔루션, 유럽 완성차 3사와 배터리 장기 계약 체결",
            "summary_kr": "LG에너지솔루션이 폭스바겐·BMW·스텔란티스와 총 15조 원 규모의 배터리 장기 공급 계약을 체결했다. 계약 기간은 2027년부터 2032년까지이며 원통형·파우치 혼합 방식으로 공급된다. 유럽 전기차 보조금 확대 정책에 힘입어 수주 모멘텀이 다시 강화되는 모습이다.",
            "why_important": "대규모 장기 수주는 실적 가시성을 높여 불확실성 프리미엄을 낮추고, 섹터 전반의 투자심리 회복을 이끌 수 있다.",
            "url": "https://finance.naver.com/news/sample3",
        },
    ],
    "international_news": [
        {
            "rank": 1,
            "title": "Fed Holds Rates Steady, Signals Two Cuts Possible in 2025",
            "summary_kr": "미국 연방준비제도가 기준금리를 5.25~5.50%로 동결하면서도 2025년 내 두 차례 인하 가능성을 점도표를 통해 시사했다. 파월 의장은 인플레이션이 목표치에 근접하고 있다며 긴축 완화 여건이 갖춰지고 있다고 언급했다. 발표 직후 S&P500과 나스닥이 동반 상승하며 위험자산 선호 심리가 빠르게 회복됐다.",
            "why_important": "연준의 인하 시그널은 글로벌 유동성 확대 기대를 높여 신흥국 증시와 성장주 전반에 긍정적 촉매가 된다.",
            "url": "https://www.investing.com/news/sample1",
        },
        {
            "rank": 2,
            "title": "NVIDIA Beats Estimates with Record $26B Revenue, AI Demand Surges",
            "summary_kr": "엔비디아가 1분기 매출 260억 달러를 기록하며 시장 예상치를 15% 초과했다. 데이터센터 부문 매출이 전년 대비 2배 이상 증가했으며, 차세대 블랙웰 GPU 수요가 공급을 크게 웃도는 상황이다. 2분기 가이던스도 280억 달러로 컨센서스를 상회해 장외 거래에서 주가가 8% 급등했다.",
            "why_important": "AI 인프라 투자 사이클이 예상보다 길고 강하다는 신호로, 반도체·클라우드·AI 소프트웨어 섹터 전반의 밸류에이션 재평가 계기가 된다.",
            "url": "https://www.investing.com/news/sample2",
        },
        {
            "rank": 3,
            "title": "US Expands Chip Export Restrictions Targeting China's AI Development",
            "summary_kr": "미국 상무부가 중국으로의 첨단 AI 반도체 및 관련 장비 수출 규제를 대폭 강화했다. 엔비디아 H20 칩과 AMD MI300X 등이 추가 규제 대상에 포함됐으며, 네덜란드 ASML의 협력도 요청했다. 중국 빅테크들은 자체 AI 칩 개발을 가속화하고 있지만 기술 격차 해소까지는 수년이 걸릴 전망이다.",
            "why_important": "수출 규제 강화는 단기적으로 엔비디아 매출에 타격을 주지만, 중장기적으로 삼성·SK하이닉스 등 한국 반도체 기업의 반사이익 가능성을 높인다.",
            "url": "https://www.investing.com/news/sample3",
        },
    ],
    "key_sectors": [
        {
            "sector": "반도체",
            "description": "AI 데이터센터 수요 폭증으로 HBM·파운드리 전 밸류체인이 슈퍼사이클에 진입했다. 미·중 규제 리스크가 변수지만 국내 기업들의 수혜 기대가 크다.",
        },
        {
            "sector": "2차전지",
            "description": "단기 전기차 수요 둔화 우려에도 유럽 정책 지원과 장기 수주 확보로 실적 가시성이 높아지고 있다. 원통형 배터리 중심의 기술 경쟁이 심화되는 중이다.",
        },
        {
            "sector": "AI·소프트웨어",
            "description": "생성형 AI 도입 가속화로 클라우드·SaaS 기업들의 ARR 성장률이 재가속되고 있다. 기업 AI 전환 수요가 내년까지 강한 투자 사이클을 뒷받침할 전망이다.",
        },
    ],
    "key_companies": [
        {
            "company": "삼성전자",
            "ticker": "005930",
            "description": "HBM3E 엔비디아 공급 승인으로 반도체 실적 반등 기대감이 높아졌다. 파운드리 수율 개선과 함께 하반기 실적 턴어라운드 가능성이 주목된다.",
        },
        {
            "company": "엔비디아",
            "ticker": "NVDA",
            "description": "AI GPU 시장 독점적 지위를 바탕으로 분기 매출 260억 달러를 달성했다. 블랙웰 아키텍처 수요가 공급을 초과해 당분간 프리미엄 가격 유지가 가능할 전망이다.",
        },
        {
            "company": "LG에너지솔루션",
            "ticker": "373220",
            "description": "유럽 완성차 3사와 15조 원 규모 배터리 장기 계약을 체결하며 수주잔고가 대폭 확대됐다. 폴란드·미국 생산기지 가동률 정상화와 맞물려 수익성 개선이 기대된다.",
        },
        {
            "company": "SK하이닉스",
            "ticker": "000660",
            "description": "HBM 시장 1위 지위를 유지하며 엔비디아에 안정적으로 공급 중이다. 삼성전자의 재진입에도 불구하고 기술 선도 우위를 바탕으로 점유율 방어가 가능할 것으로 보인다.",
        },
    ],
}

sample_market = {
    "kospi": {"price": 2_587.45, "change": 18.32, "change_pct": 0.71},
    "nasdaq": {"price": 18_342.56, "change": 215.34, "change_pct": 1.19},
    "usdkrw": {"price": 1_374.20, "change": -3.80, "change_pct": -0.28},
}

if __name__ == "__main__":
    print("Notion 테스트 저장 시작...")
    url = save_to_notion(
        summary=sample_summary,
        domestic_themes=sample_domestic_themes,
        international_themes=sample_international_themes,
        market_data=sample_market,
        date_str="2026-04-30",
    )
    if url:
        print(f"\n저장 완료!\n{url}")
    else:
        print("\n저장 실패 — .env 파일과 Notion 설정을 확인하세요.")
