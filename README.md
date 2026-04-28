# 주식 뉴스 자동 스크랩 앱

이 앱은 매일 한국 시간 오전 7시에 국내 뉴스와 해외 뉴스를 모아서 정리하고, Notion 데이터베이스에 저장합니다.

## 기능
- 🇰🇷 국내 뉴스: 네이버 경제 뉴스에서 주요 뉴스 수집
- 🌎 해외 뉴스: Investing.com에서 주요 뉴스 수집
- 📊 마크다운 보고서: `output/YYYY-MM-DD.md` 파일 생성
- 🗄️ Notion 저장: 뉴스를 데이터베이스에 자동 저장
- ⏰ 자동 실행: GitHub Actions로 매일 오전 7시 실행

## 준비물
1. **Python 3.11+** 설치
2. **GitHub 계정** (자동 실행용)
3. **Notion 계정** (데이터베이스 저장용)

## Notion 설정
1. [Notion 개발자 사이트](https://developers.notion.com/)에서 통합 만들기
2. `NOTION_TOKEN` 복사
3. 데이터베이스 만들고 통합 연결
4. 데이터베이스 URL에서 ID 추출
5. `.env` 파일에 토큰과 ID 입력

### 데이터베이스 속성 (필수)
- **Title** (제목) - Title 타입

### 데이터베이스 속성 (선택)
- **Date** (날짜) - Date 타입
- **Region** (지역) - Select 타입 (국내/해외)
- **Source** (출처) - Text 타입
- **URL** (링크) - URL 타입

## 로컬 실행
```bash
# 1. 프로젝트 폴더로 이동
cd stock-news-app

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 실행
python main.py
```

## GitHub Actions 자동 실행 설정

### 1. GitHub에 코드 업로드
```bash
# GitHub에 새 저장소 만들기
# 로컬에서 Git 초기화
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. GitHub Secrets 설정
1. GitHub 저장소 → Settings → Secrets and variables → Actions
2. **NOTION_TOKEN** 추가: Notion 통합 토큰 값
3. **NOTION_DATABASE_ID** 추가: 데이터베이스 ID 값

### 3. 워크플로우 확인
- `.github/workflows/schedule.yml` 파일이 자동으로 실행됩니다
- 매일 오전 7시(KST)에 실행
- 실행 결과는 Actions 탭에서 확인 가능

### 4. 수동 실행 (테스트용)
- GitHub Actions → schedule 워크플로우 → Run workflow 클릭

## 파일 구조
```
stock-news-app/
├── .github/workflows/schedule.yml    # GitHub Actions 설정
├── config.py                         # 설정 파일
├── main.py                          # 메인 실행 파일
├── notion_api.py                    # Notion API 연동
├── utils.py                         # 유틸리티 함수
├── news_sources/                    # 뉴스 수집 모듈
│   ├── domestic.py                  # 국내 뉴스
│   └── overseas.py                  # 해외 뉴스
├── output/                          # 생성된 보고서
├── logs/                           # 실행 로그
├── requirements.txt                 # Python 의존성
├── .env                            # 환경 변수 (GitHub 미업로드)
└── .gitignore                      # Git 제외 파일
```

## 로그 및 보고서
- **보고서**: `output/YYYY-MM-DD.md` - 일일 뉴스 요약
- **로그**: `logs/` - 실행 기록
- **GitHub Actions**: Actions 탭에서 실행 결과 확인

## 문제 해결
- **Notion 연결 실패**: 토큰과 데이터베이스 ID 확인
- **속성 오류**: Notion 데이터베이스에 Title 속성 추가
- **실행 실패**: GitHub Secrets 제대로 설정되었는지 확인
