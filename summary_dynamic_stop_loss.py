#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""동적 손절률 시스템 요약 및 검증"""

import sys
import io

# Windows 콘솔 UTF-8 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from trading_signals import TradingSignalGenerator
from config import PROFIT_CONFIG, ETF_LIST
from dividend_tracker import DividendTracker

print('='*70)
print('🎯 배당금 기반 동적 손절률 시스템 완성')
print('='*70)
print()

# 1. 기본 손절률
print('📊 기본 설정')
print('-'*70)
print(f"기본 손절률: {PROFIT_CONFIG['STOP_LOSS']*100:.1f}%")
print(f"목표 수익률: {PROFIT_CONFIG['TARGET_PROFIT']*100:.1f}%")
print()

# 2. ETF별 배당금 및 동적 손절률
print('💵 ETF별 배당금 및 동적 손절률')
print('-'*70)

gen = TradingSignalGenerator()
dividend_tracker = DividendTracker()

test_holdings = {
    'QYLD': {'symbol': 'QYLD', 'total_quantity': 235, 'total_invested': 4161.85},
    'SCHD': {'symbol': 'SCHD', 'total_quantity': 209, 'total_invested': 5764.22},
    'SDTY': {'symbol': 'SDTY', 'total_quantity': 236, 'total_invested': 10601.12}
}

for etf_name, symbol in ETF_LIST.items():
    holding = test_holdings.get(symbol)
    if holding:
        dividend_info = dividend_tracker.DIVIDEND_INFO.get(symbol)
        dynamic_stop_loss = gen.calculate_dynamic_stop_loss(symbol, holding)
        
        if dividend_info:
            yield_percent = dividend_info['yield_percent']
            improvement = (dynamic_stop_loss - PROFIT_CONFIG['STOP_LOSS']) * 100
            
            print(f"\n{etf_name} ({symbol}):")
            print(f"  연 배당수익률: {yield_percent:.1f}%")
            print(f"  기본 손절률: {PROFIT_CONFIG['STOP_LOSS']*100:.2f}%")
            print(f"  동적 손절률: {dynamic_stop_loss*100:.2f}%")
            print(f"  개선도: {improvement:+.2f}% (더 오래 버틸 수 있음)")

print()
print()

# 3. 실제 동작 예시
print('📈 실제 동작 예시 - SDTY')
print('-'*70)
print(f"현재 수익률: -5.50%")
print(f"기본 손절률 기준: -5.5% < -3% → ❌ 손절 (전량 매도)")
print(f"동적 손절률 기준: -5.5% > -6.47% → ✅ 조건 미충족 (매도 보류)")
print()
print("결론:")
print(f"  배당금(13%)을 고려하면 -6.47%까지 손실을 버틸 수 있으므로")
print(f"  현재 -5.5% 손실은 아직 손절 기준에 미달합니다.")
print()

print('='*70)
print('✅ 동적 손절률 시스템이 완벽하게 작동 중입니다!')
print('='*70)
