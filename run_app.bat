@echo off
cd /d "%~dp0"

REM 가상환경이 있는지 확인
if not exist "venv\Scripts\activate.bat" (
    echo 가상환경을 생성합니다...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
) else (
    call venv\Scripts\activate.bat
)

python app.py
