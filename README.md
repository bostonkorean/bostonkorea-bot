# 보스톤코리아 소셜미디어 봇

보스톤코리아 뉴스 기사를 X(트위터)와 인스타그램용 소셜미디어 포스트로 자동 변환하는 데스크탑 앱입니다.

## 기능

- 보스톤코리아 최신 기사 목록 조회 (카테고리별 필터링)
- 기사 선택 시 X/인스타그램용 텍스트 자동 생성
- 해시태그 자동 생성
- 클립보드 복사 기능
- URL 직접 입력 지원

## Windows에서 사용하기

### 방법 1: exe 파일 다운로드 (권장)

1. [Releases](../../releases) 페이지에서 최신 `BostonKoreaBot.exe` 다운로드
2. 더블클릭으로 실행

### 방법 2: Python으로 직접 실행

```bash
# 저장소 클론
git clone https://github.com/bostonkorean/bostonkorea-bot.git
cd bostonkorea-bot

# 실행 (Windows)
run_app.bat

# 또는 수동으로
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 방법 3: 직접 exe 빌드

```bash
build_windows.bat
# 빌드 완료 후: dist\BostonKoreaBot.exe
```

## 사용 방법

1. 앱 실행 후 카테고리 선택 (전체, 미국, 한국, 경제 등)
2. 왼쪽 기사 목록에서 원하는 기사 클릭
3. 오른쪽에 X/인스타그램용 텍스트가 자동 생성됨
4. "복사" 버튼으로 클립보드에 복사
5. 해당 소셜미디어에 붙여넣기
