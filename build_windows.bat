@echo off
echo ========================================
echo  보스톤코리아 봇 - Windows 빌드
echo ========================================
echo.

REM Python 가상환경 생성
echo [1/4] 가상환경 생성 중...
python -m venv venv
call venv\Scripts\activate.bat

REM 패키지 설치
echo [2/4] 패키지 설치 중...
pip install -r requirements.txt -q

REM PyInstaller로 exe 생성
echo [3/4] exe 파일 생성 중...
pyinstaller --noconfirm --onefile --windowed ^
    --name "BostonKoreaBot" ^
    --add-data "bostonkorea_bot.py;." ^
    --add-data "config_manager.py;." ^
    --add-data "social_poster.py;." ^
    --add-data "media_generator.py;." ^
    --hidden-import customtkinter ^
    --hidden-import tweepy ^
    --hidden-import instagrapi ^
    --hidden-import imageio ^
    --hidden-import PIL ^
    --collect-all customtkinter ^
    app.py

echo [4/4] 정리 중...
rmdir /s /q build 2>nul
del /q BostonKoreaBot.spec 2>nul

echo.
echo ========================================
echo  빌드 완료!
echo  실행 파일: dist\BostonKoreaBot.exe
echo ========================================
pause
