#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""동적 손절률 계산 테스트"""

import sys
import io

# Windows 콘솔 UTF-8 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from trading_signals import TradingSignalGenerator
from config import PROFIT_CONFIG

# 테스트 데이터
test_holdings = {
    'QYLD': {'symbol': 'QYLD', 'total_quantity': 235, 'total_invested': 4161.85},
    'SCHD': {'symbol': 'SCHD', 'total_quantity': 209, 'total_invested': 5764.22},
    'SDTY': {'symbol': 'SDTY', 'total_quantity': 236, 'total_invested': 10601.12}
}

gen = TradingSignalGenerator()

print('='*70)
print('동적 손절률 계산 테스트')
print('='*70)
print()
print(f'기본 손절률: {PROFIT_CONFIG["STOP_LOSS"]*100:.2f}%')
print()

for symbol, holding in test_holdings.items():
    dynamic_stop_loss = gen.calculate_dynamic_stop_loss(symbol, holding)
    improvement = (dynamic_stop_loss - PROFIT_CONFIG['STOP_LOSS']) * 100
    
    dividend_info = gen.DIVIDEND_INFO.get(symbol)
    yield_percent = dividend_info.get('yield_percent', 0) if dividend_info else 0
    
    print(f'{symbol}:')
    print(f'  연 배당수익률: {yield_percent:.1f}%')
    print(f'  기본 손절률: {PROFIT_CONFIG["STOP_LOSS"]*100:.2f}%')
    print(f'  동적 손절률: {dynamic_stop_loss*100:.2f}%')
    print(f'  개선도: {improvement:+.2f}% (더 오래 버틸 수 있음)')
    print()

print('='*70)
print('설명:')
print('  - 배당수익률이 높을수록 손절률이 낮아짐 (더 오래 버틸 수 있음)')
print('  - QYLD/SDTY: 12% 이상 배당 → 4개월 버틸 수 있도록 계산')
print('  - SCHD: 3-12% 배당 → 5개월 버틸 수 있도록 계산')
print('  - 안전마진 80% 적용 (배당금의 80%만 손절률에 반영)')
print('='*70)
