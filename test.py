#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 스크립트
프로그램의 기본 기능을 테스트합니다.
"""

import logging
from datetime import datetime
from etf_analyzer import ETFAnalyzer
from trading_signals import TradingSignalGenerator
from config import ETF_LIST, LOG_PATH
import os

# 로깅 설정
os.makedirs(LOG_PATH, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_PATH}/test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_etf_analyzer():
    """ETF 분석 기능 테스트"""
    print("\n" + "="*60)
    print("📊 ETF Analyzer 테스트")
    print("="*60 + "\n")
    
    analyzer = ETFAnalyzer()
    
    # 테스트할 ETF
    test_etf = "069500.KS"  # TIGER 200
    
    try:
        print(f"데이터 수집 중: {test_etf}...")
        data = analyzer.fetch_etf_data(test_etf, period="3mo")
        
        if data is None:
            print("❌ 데이터 수집 실패")
            return False
        
        print(f"✓ {len(data)} 행의 데이터 수집 완료\n")
        
        # 분석 실행
        analysis = analyzer.analyze_etf(test_etf)
        
        if analysis is None:
            print("❌ 분석 실패")
            return False
        
        # 결과 출력
        print("\n📈 분석 결과:")
        print(f"  현재 가격: {analysis['returns']['current_price']:.0f}원")
        print(f"  1일 수익률: {analysis['returns']['return_1d']:.2f}%")
        print(f"  1개월 수익률: {analysis['returns']['return_1m']:.2f}%")
        print(f"  3개월 수익률: {analysis['returns']['return_3m']:.2f}%\n")
        
        print("  이동평균:")
        print(f"    단기 MA(20): {analysis['moving_average']['ma_short']}")
        print(f"    장기 MA(60): {analysis['moving_average']['ma_long']}")
        print(f"    신호: {analysis['moving_average']['signal']}\n")
        
        print("  RSI:")
        print(f"    값: {analysis['rsi']['rsi']}")
        print(f"    신호: {analysis['rsi']['signal']}\n")
        
        print("  MACD:")
        print(f"    MACD: {analysis['macd']['macd']}")
        print(f"    신호선: {analysis['macd']['signal_line']}")
        print(f"    MACD 신호: {analysis['macd']['signal']}\n")
        
        print("✓ ETF Analyzer 테스트 성공\n")
        return True
    
    except Exception as e:
        logger.error(f"테스트 실패: {str(e)}", exc_info=True)
        print(f"❌ 테스트 실패: {str(e)}\n")
        return False


def test_signal_generator(analysis):
    """거래 신호 생성 기능 테스트"""
    print("="*60)
    print("🎯 Trading Signal Generator 테스트")
    print("="*60 + "\n")
    
    try:
        generator = TradingSignalGenerator()
        
        # 신호 생성
        signal = generator.generate_signal(analysis)
        
        print(f"신호: {signal['signal']}")
        print(f"신뢰도: {signal['confidence']:.1f}%")
        print(f"현재 가격: {signal['current_price']:.0f}원\n")
        
        print(f"신호 강도:")
        print(f"  매수 신호: {signal['buy_signals']}개")
        print(f"  매도 신호: {signal['sell_signals']}개\n")
        
        # 포지션 추가 테스트
        print("포지션 추가 테스트:")
        generator.add_position("069500.KS", 12345, 10, "테스트 매입")
        print("✓ 포지션 추가 완료\n")
        
        # 포지션 상태 확인
        status = generator.get_position_status("069500.KS", signal['current_price'])
        if status:
            print(f"포지션 상태:")
            print(f"  수량: {status['total_quantity']}주")
            print(f"  평균 매입가: {status['avg_entry_price']:.0f}원")
            print(f"  현재 가격: {status['current_price']:.0f}원")
            print(f"  수익률: {status['returns_pct']:.2f}%\n")
        
        # 포지션 종료 테스트
        print("포지션 종료 테스트:")
        closed = generator.close_position("069500.KS", signal['current_price'], quantity=5)
        if closed:
            print(f"✓ 포지션 종료 (수익률: {closed[0]['returns_pct']:.2f}%)\n")
        
        print("✓ Signal Generator 테스트 성공\n")
        return True
    
    except Exception as e:
        logger.error(f"테스트 실패: {str(e)}", exc_info=True)
        print(f"❌ 테스트 실패: {str(e)}\n")
        return False


def test_all_etfs():
    """모든 ETF 분석 테스트"""
    print("="*60)
    print("📋 모든 ETF 분석 테스트")
    print("="*60 + "\n")
    
    analyzer = ETFAnalyzer()
    generator = TradingSignalGenerator()
    
    results = {}
    
    for etf_name, symbol in ETF_LIST.items():
        try:
            print(f"분석 중: {etf_name} ({symbol})...", end=" ")
            
            analysis = analyzer.analyze_etf(symbol)
            
            if analysis is None:
                print("❌ 실패")
                results[etf_name] = "FAIL"
                continue
            
            signal = generator.generate_signal(analysis)
            results[etf_name] = signal['signal']
            
            print(f"✓ {signal['signal']} ({signal['confidence']:.0f}%)")
        
        except Exception as e:
            logger.error(f"{etf_name} 분석 실패: {str(e)}")
            results[etf_name] = "ERROR"
            print(f"❌ {str(e)}")
    
    # 결과 요약
    print("\n결과 요약:")
    for etf_name, signal in results.items():
        print(f"  {etf_name}: {signal}")
    
    return True


def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("🧪 ETF 자동 거래 프로그램 테스트")
    print("="*60)
    
    try:
        # 1. ETF Analyzer 테스트
        if not test_etf_analyzer():
            return False
        
        # 분석 결과 얻기
        analyzer = ETFAnalyzer()
        analysis = analyzer.analyze_etf("069500.KS")
        
        if analysis is None:
            print("❌ 분석이 실패하여 추가 테스트를 진행할 수 없습니다.")
            return False
        
        # 2. Signal Generator 테스트
        if not test_signal_generator(analysis):
            return False
        
        # 3. 모든 ETF 분석 테스트
        test_all_etfs()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("="*60)
        print("\n프로그램이 정상적으로 작동하는 것 같습니다.")
        print("이제 'python main.py' 로 본 프로그램을 실행할 수 있습니다.")
        
        return True
    
    except Exception as e:
        logger.error(f"테스트 중 오류: {str(e)}", exc_info=True)
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        print(f"로그를 확인하세요: {LOG_PATH}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
