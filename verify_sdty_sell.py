#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SDTY SELL 신호 검증"""

import sys
import io

# Windows 콘솔 UTF-8 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from etf_analyzer import ETFAnalyzer
from trading_signals import TradingSignalGenerator
from config import PROFIT_CONFIG

print('='*70)
print('🔍 SDTY SELL 신호 검증')
print('='*70)
print()

analyzer = ETFAnalyzer()
signal_gen = TradingSignalGenerator()

# SDTY 분석
print('1️⃣  SDTY 기술적 분석')
print('-'*70)

analysis = analyzer.analyze_etf('SDTY')

if analysis:
    print(f"현재가: ${analysis['returns']['current_price']:.2f}")
    print()
    
    # 이동평균선
    ma = analysis['moving_average']
    print(f"이동평균선:")
    print(f"  MA20: ${ma['ma_short']:.2f}")
    print(f"  MA60: ${ma['ma_long']:.2f}")
    print(f"  신호: {ma['signal']}")
    print()
    
    # RSI
    rsi = analysis['rsi']
    print(f"RSI:")
    print(f"  값: {rsi['rsi']:.2f}")
    print(f"  신호: {rsi['signal']}")
    print()
    
    # MACD
    macd = analysis['macd']
    print(f"MACD:")
    print(f"  MACD: {macd['macd']:.4f}")
    print(f"  Signal: {macd['signal_line']:.4f}")
    print(f"  신호: {macd['signal']}")
    print()
    
    # 수익률
    returns = analysis['returns']
    print(f"수익률:")
    print(f"  1주: {returns.get('return_1w', 'N/A')}%")
    print(f"  1개월: {returns.get('return_1m', 'N/A')}%")
    print()
    
    # 거래 신호 생성
    print('2️⃣  거래 신호')
    print('-'*70)
    
    signal = signal_gen.generate_signal(analysis)
    
    print(f"최종 신호: {signal['signal']}")
    print(f"신뢰도: {signal['confidence']:.0f}%")
    print(f"매수 신호: {signal['buy_signals']}")
    print(f"매도 신호: {signal['sell_signals']}")
    print()
    
    # 손절 신호 여부 확인
    print('3️⃣  손절 신호 분석')
    print('-'*70)
    
    base_stop_loss = PROFIT_CONFIG['STOP_LOSS']
    returns_1m = returns.get('return_1m', 0)
    
    print(f"1개월 수익률: {returns_1m}%")
    print(f"기본 손절률: {base_stop_loss*100:.2f}%")
    
    if returns_1m <= base_stop_loss * 100:
        print(f"❌ 손절 조건 충족: {returns_1m}% <= {base_stop_loss*100:.2f}%")
    else:
        print(f"✅ 손절 조건 미충족: {returns_1m}% > {base_stop_loss*100:.2f}%")
    
    print()
    
    # 동적 손절률
    print('4️⃣  동적 손절률')
    print('-'*70)
    
    holding = {'total_quantity': 236, 'total_invested': 10601.12}
    dynamic_stop_loss = signal_gen.calculate_dynamic_stop_loss('SDTY', holding)
    
    print(f"동적 손절률: {dynamic_stop_loss*100:.2f}%")
    print(f"현재 수익률: {returns_1m:.2f}%")
    
    if returns_1m <= dynamic_stop_loss * 100:
        print(f"❌ 동적 손절 조건 충족: {returns_1m:.2f}% <= {dynamic_stop_loss*100:.2f}%")
    else:
        print(f"✅ 동적 손절 조건 미충족: {returns_1m:.2f}% > {dynamic_stop_loss*100:.2f}%")
    
    print()
    
    # 결론
    print('5️⃣  결론')
    print('-'*70)
    
    print(f"신호: {signal['signal']}")
    print()
    
    if signal['signal'] == 'SELL':
        print("✅ SELL 신호는 기술적 분석 기반으로 맞습니다.")
        print()
        print("하지만 매도 수량이 0인 이유:")
        print(f"  - 1개월 수익률: {returns_1m:.2f}%")
        print(f"  - 동적 손절률: {dynamic_stop_loss*100:.2f}%")
        print(f"  - {returns_1m:.2f}% > {dynamic_stop_loss*100:.2f}% → 손절 기준 미달")
        print()
        print("→ 기술적으로 SELL이나 동적 손절률로 보호되고 있습니다.")
        print("→ 손실을 버틸 수 있는 추가 여지가 있으므로 매도 보류 중입니다.")
    else:
        print(f"신호: {signal['signal']} (SELL 아님)")

print()
print('='*70)
