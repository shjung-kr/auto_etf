#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 시작 가이드
ETF 분석 프로그램을 처음 사용하는 경우 이 스크립트를 실행하세요.
"""

import os
import sys
from pathlib import Path


def create_directories():
    """필요한 디렉토리 생성"""
    print("📁 디렉토리 생성 중...")
    
    dirs = ['data', 'logs', 'config']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ {dir_name}/ 생성됨")
    
    print()


def check_python_version():
    """Python 버전 확인"""
    print("🐍 Python 버전 확인 중...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} (Python 3.8 이상 필요)")
        return False


def install_dependencies():
    """의존 라이브러리 설치"""
    print("\n📦 의존 라이브러리 설치 중...")
    print("(이것은 몇 분 걸릴 수 있습니다)\n")
    
    result = os.system('pip install -r requirements.txt')
    
    if result == 0:
        print("\n✓ 라이브러리 설치 완료")
        return True
    else:
        print("\n✗ 라이브러리 설치 실패")
        return False


def setup_env_file():
    """환경 변수 파일 설정"""
    print("\n⚙️  환경 변수 설정")
    
    if os.path.exists('.env'):
        print("✓ .env 파일이 이미 존재합니다.")
        return
    
    if os.path.exists('.env.example'):
        response = input("  → .env.example을 .env로 복사할까요? (y/n): ").strip().lower()
        if response == 'y':
            import shutil
            shutil.copy('.env.example', '.env')
            print("✓ .env 파일 생성됨")
            print("  → .env 파일을 편집하고 필요한 정보를 입력하세요.")
    else:
        print("⚠ .env.example 파일을 찾을 수 없습니다.")


def test_imports():
    """라이브러리 import 테스트"""
    print("\n🔍 라이브러리 테스트 중...")
    
    try:
        import pandas
        print("✓ pandas")
        import numpy
        print("✓ numpy")
        import yfinance
        print("✓ yfinance")
        import requests
        print("✓ requests")
        from apscheduler.schedulers.background import BackgroundScheduler
        print("✓ apscheduler")
        
        print("\n✓ 모든 라이브러리 정상 설치됨")
        return True
    except ImportError as e:
        print(f"\n✗ 라이브러리 로드 실패: {e}")
        return False


def test_data_fetch():
    """데이터 수집 테스트"""
    print("\n🌐 데이터 수집 테스트 중...")
    
    try:
        import yfinance as yf
        
        print("  → TIGER 200 (069500.KS) 테스트 중...")
        data = yf.download('069500.KS', period='1d', progress=False)
        
        if not data.empty:
            print(f"✓ 데이터 수집 성공")
            print(f"  마지막 가격: {data['Close'].iloc[-1]:.2f}")
            return True
        else:
            print("✗ 데이터를 가져올 수 없습니다.")
            return False
    except Exception as e:
        print(f"✗ 데이터 수집 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("="*60)
    print("🚀 ETF 자동 거래 프로그램 - 빠른 시작")
    print("="*60)
    print()
    
    # 1. Python 버전 확인
    if not check_python_version():
        print("\n❌ Python 3.8 이상을 설치하세요.")
        return False
    
    # 2. 디렉토리 생성
    create_directories()
    
    # 3. 의존 라이브러리 설치
    if not install_dependencies():
        print("\n❌ 라이브러리 설치에 실패했습니다.")
        print("   pip install -r requirements.txt 를 수동으로 실행하세요.")
        return False
    
    # 4. Import 테스트
    if not test_imports():
        print("\n❌ 라이브러리 로드에 실패했습니다.")
        return False
    
    # 5. 데이터 수집 테스트
    if not test_data_fetch():
        print("\n⚠ 데이터 수집에 실패했습니다.")
        print("  네트워크 연결을 확인하세요.")
    else:
        print()
    
    # 6. 환경 변수 설정
    setup_env_file()
    
    print("\n" + "="*60)
    print("✅ 설정 완료!")
    print("="*60)
    print("\n다음 단계:")
    print("  1. .env 파일을 편집하여 이메일/Discord 설정 (선택사항)")
    print("  2. config.py에서 ETF 목록과 기본값 커스터마이징")
    print("  3. python main.py 로 프로그램 실행")
    print("\n📚 더 자세한 정보는 README.md를 참고하세요.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
