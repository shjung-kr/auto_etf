#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용 예시 (Example Usage)
프로그램을 프로그래밍 방식으로 사용하는 방법을 보여줍니다.
"""

from etf_analyzer import ETFAnalyzer
from trading_signals import TradingSignalGenerator
from notification_manager import NotificationManager
from config import ETF_LIST
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_simple_analysis():
    """예시 1: 간단한 분석"""
    print("\n" + "="*60)
    print("예시 1: 단일 ETF 간단 분석")
    print("="*60)
    
    analyzer = ETFAnalyzer()
    
    # TIGER 200 분석
    analysis = analyzer.analyze_etf("069500.KS")
    
    if analysis:
        print(f"\n📊 TIGER 200 분석 결과:")
        print(f"  현재가: {analysis['returns']['current_price']:.0f}원")
        print(f"  1개월 수익률: {analysis['returns']['return_1m']:.2f}%")
        print(f"  이동평균 신호: {analysis['moving_average']['signal']}")
        print(f"  RSI: {analysis['rsi']['rsi']:.2f}")


def example_2_signal_generation():
    """예시 2: 거래 신호 생성"""
    print("\n" + "="*60)
    print("예시 2: 거래 신호 생성")
    print("="*60)
    
    analyzer = ETFAnalyzer()
    signal_gen = TradingSignalGenerator()
    
    # 분석
    analysis = analyzer.analyze_etf("069500.KS")
    
    if analysis:
        # 신호 생성
        signal = signal_gen.generate_signal(analysis)
        
        print(f"\n🎯 거래 신호:")
        print(f"  신호: {signal['signal']}")
        print(f"  신뢰도: {signal['confidence']:.0f}%")
        print(f"  현재가: {signal['current_price']:.0f}원")


def example_3_portfolio_management():
    """예시 3: 포트폴리오 관리"""
    print("\n" + "="*60)
    print("예시 3: 포트폴리오 관리")
    print("="*60)
    
    signal_gen = TradingSignalGenerator()
    
    # 포지션 추가
    print("\n📍 포지션 추가:")
    signal_gen.add_position("069500.KS", 12345, 10, "매수 신호로 진입")
    print("✓ TIGER 200: 10주 @ 12,345원 추가")
    
    # 포지션 상태 확인
    print("\n📊 포지션 상태:")
    status = signal_gen.get_position_status("069500.KS", 12800)
    if status:
        print(f"  보유수량: {status['total_quantity']}주")
        print(f"  평균매입가: {status['avg_entry_price']:.0f}원")
        print(f"  현재가: {status['current_price']:.0f}원")
        print(f"  미실현손익: {status['unrealized_profit']:,.0f}원")
        print(f"  수익률: {status['returns_pct']:.2f}%")
    
    # 포지션 종료
    print("\n🔚 포지션 종료:")
    closed = signal_gen.close_position("069500.KS", 12800, quantity=10)
    if closed:
        trade = closed[0]
        print(f"  청산가: {trade['exit_price']:.0f}원")
        print(f"  수익률: {trade['returns_pct']:.2f}%")
        print(f"  이익: {trade['profit']:,.0f}원")


def example_4_multiple_etfs():
    """예시 4: 여러 ETF 동시 분석"""
    print("\n" + "="*60)
    print("예시 4: 여러 ETF 동시 분석")
    print("="*60)
    
    analyzer = ETFAnalyzer()
    signal_gen = TradingSignalGenerator()
    
    print("\n분석 결과:")
    print("-" * 60)
    
    for etf_name, symbol in list(ETF_LIST.items())[:3]:  # 처음 3개만
        try:
            analysis = analyzer.analyze_etf(symbol)
            if analysis:
                signal = signal_gen.generate_signal(analysis)
                
                status = "🟢" if signal['signal'] == 'BUY' else "🔴" if signal['signal'] == 'SELL' else "⚪"
                print(f"{status} {etf_name}: {signal['signal']} ({signal['confidence']:.0f}%)")
        
        except Exception as e:
            print(f"❌ {etf_name}: 분석 실패")


def example_5_notification():
    """예시 5: 알림 전송"""
    print("\n" + "="*60)
    print("예시 5: 알림 전송")
    print("="*60)
    
    analyzer = ETFAnalyzer()
    signal_gen = TradingSignalGenerator()
    notifier = NotificationManager()
    
    # 분석 및 신호 생성
    analysis = analyzer.analyze_etf("069500.KS")
    if analysis:
        signal = signal_gen.generate_signal(analysis)
        
        # 알림 전송 (콘솔에만)
        print("\n알림 메시지:")
        notifier.send_all_notifications(signal)


def example_6_advanced_analysis():
    """예시 6: 고급 분석"""
    print("\n" + "="*60)
    print("예시 6: 고급 분석 - 개별 지표")
    print("="*60)
    
    analyzer = ETFAnalyzer()
    
    # 데이터 수집
    analyzer.fetch_etf_data("069500.KS", period="6mo")
    
    # 각 지표별 분석
    print("\n📈 이동평균선:")
    ma = analyzer.calculate_moving_averages("069500.KS")
    print(f"  현재가: {ma['current_price']:.0f}원")
    print(f"  MA20: {ma['ma_short']:.0f}원")
    print(f"  MA60: {ma['ma_long']:.0f}원")
    print(f"  신호: {ma['signal']}")
    
    print("\n📊 RSI:")
    rsi = analyzer.calculate_rsi("069500.KS")
    print(f"  RSI: {rsi['rsi']:.2f}")
    print(f"  신호: {rsi['signal']}")
    
    print("\n📉 MACD:")
    macd = analyzer.calculate_macd("069500.KS")
    print(f"  MACD: {macd['macd']:.4f}")
    print(f"  신호선: {macd['signal_line']:.4f}")
    print(f"  신호: {macd['signal']}")


def example_7_backtest():
    """예시 7: 백테스팅 예시"""
    print("\n" + "="*60)
    print("예시 7: 백테스팅")
    print("="*60)
    
    signal_gen = TradingSignalGenerator()
    
    # 모의 거래 시뮬레이션
    print("\n모의 거래:")
    
    trades = [
        ("069500.KS", 10000, 10, 10200, "첫 번째 거래"),  # +2% 수익
        ("069500.KS", 10200, 10, 9900, "두 번째 거래"),   # -3% 손실
        ("069500.KS", 9900, 10, 10500, "세 번째 거래"),   # +5.5% 수익
    ]
    
    for symbol, entry_price, quantity, exit_price, note in trades:
        signal_gen.add_position(symbol, entry_price, quantity, note)
        closed = signal_gen.close_position(symbol, exit_price, quantity)
        
        if closed:
            trade = closed[0]
            print(f"  {note}: {trade['returns_pct']:.2f}% ({trade['profit']:+.0f}원)")
    
    # 성과 분석
    print("\n📊 성과 분석:")
    returns = signal_gen.calculate_portfolio_returns()
    print(f"  총 거래: {returns['total_trades']}회")
    print(f"  총 이익: {returns['total_profit']:,.0f}원")
    print(f"  승률: {returns['win_rate']:.1f}%")
    print(f"  거래당 평균: {returns['avg_profit_per_trade']:,.0f}원")


def main():
    """모든 예시 실행"""
    print("\n" + "="*60)
    print("🚀 ETF 자동 거래 프로그램 - 사용 예시")
    print("="*60)
    
    try:
        example_1_simple_analysis()
        example_2_signal_generation()
        example_3_portfolio_management()
        example_4_multiple_etfs()
        example_5_notification()
        example_6_advanced_analysis()
        example_7_backtest()
        
        print("\n" + "="*60)
        print("✅ 모든 예시 완료")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        print("\nlog 파일을 확인하세요.")


if __name__ == "__main__":
    main()
