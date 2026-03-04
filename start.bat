@echo off
REM ETF 자동 거래 프로그램 시작 스크립트

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo ETF 자동 거래 프로그램
echo ============================================================
echo.

REM Python 설치 여부 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python 3.8 이상을 설치한 후 다시 실행하세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python 설치 확인됨
python --version

REM 요구 사항 설치 여부 확인
if not exist venv (
    echo.
    echo 📦 가상 환경 생성 중...
    python -m venv venv
    echo ✓ 가상 환경 생성 완료
    
    echo.
    echo 📦 의존 라이브러리 설치 중...
    call venv\Scripts\activate.bat
    pip install -q -r requirements.txt
    if errorlevel 1 (
        echo ❌ 라이브러리 설치 실패
        pause
        exit /b 1
    )
    echo ✓ 라이브러리 설치 완료
) else (
    call venv\Scripts\activate.bat
)

echo.
echo ============================================================
echo 프로그램을 선택하세요:
echo ============================================================
echo 1. 빠른 시작 (처음 사용)
echo 2. 테스트 실행
echo 3. 메인 프로그램 실행
echo 4. 종료
echo.

set /p choice="선택 (1-4): "

if "%choice%"=="1" (
    echo.
    python quick_start.py
) else if "%choice%"=="2" (
    echo.
    python test.py
) else if "%choice%"=="3" (
    echo.
    python main.py
) else if "%choice%"=="4" (
    echo.
    echo 프로그램을 종료합니다.
    exit /b 0
) else (
    echo.
    echo ❌ 잘못된 선택입니다.
    pause
    exit /b 1
)

pause
