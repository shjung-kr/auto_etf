#!/bin/bash

# ETF 자동 거래 프로그램 시작 스크립트 (Linux/Mac)

echo ""
echo "============================================================"
echo "ETF 자동 거래 프로그램"
echo "============================================================"
echo ""

# Python 설치 여부 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python이 설치되지 않았습니다."
    echo "Python 3.8 이상을 설치한 후 다시 실행하세요."
    exit 1
fi

echo "✓ Python 설치 확인됨"
python3 --version

# 가상 환경 생성 및 활성화
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 가상 환경 생성 중..."
    python3 -m venv venv
    echo "✓ 가상 환경 생성 완료"
    
    echo ""
    echo "📦 의존 라이브러리 설치 중..."
    source venv/bin/activate
    pip install -q -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 라이브러리 설치 실패"
        exit 1
    fi
    echo "✓ 라이브러리 설치 완료"
else
    source venv/bin/activate
fi

echo ""
echo "============================================================"
echo "프로그램을 선택하세요:"
echo "============================================================"
echo "1. 빠른 시작 (처음 사용)"
echo "2. 테스트 실행"
echo "3. 메인 프로그램 실행"
echo "4. 종료"
echo ""

read -p "선택 (1-4): " choice

case $choice in
    1)
        echo ""
        python3 quick_start.py
        ;;
    2)
        echo ""
        python3 test.py
        ;;
    3)
        echo ""
        python3 main.py
        ;;
    4)
        echo ""
        echo "프로그램을 종료합니다."
        exit 0
        ;;
    *)
        echo ""
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac
